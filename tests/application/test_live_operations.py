from smart_money.application.live_discovery import (
    LiveProviderFailureEvidence,
    ProviderRetryPolicy,
    start_live_session,
)
from smart_money.core.ids import deterministic_id
from smart_money.application.live_operations import (
    build_retry_schedule,
    capture_live_replay,
    commit_live_payloads,
    deduplicate_live_candidates,
    evaluate_operational_readiness,
    monitor_provider_health,
    recover_live_failure,
    refresh_live_candidates,
    refresh_live_dashboard,
    run_live_rpc_session,
)
from smart_money.ingestion.contracts import EvidencePayload


class _RecordingLedger:
    def __init__(self) -> None:
        self.appended = []

    def append(self, payload: EvidencePayload) -> str:
        canonical_id = payload.get_canonical_id()
        self.appended.append(canonical_id)
        return canonical_id


def _fetcher_factory(slots: list[int]):
    calls = iter(slots)

    def fetch(method: str, params: dict) -> dict:
        assert method == "getSlot"
        assert params["commitment"] == "confirmed"
        return {"slot": next(calls)}

    return fetch


def test_live_rpc_session_run_is_deterministic() -> None:
    session = start_live_session("solana-production", 100)
    first, checkpoints = run_live_rpc_session(
        session, _fetcher_factory([101, 103, 106]), start_cursor=100, max_polls=3
    )
    replayed, _ = run_live_rpc_session(
        session, _fetcher_factory([101, 103, 106]), start_cursor=100, max_polls=3
    )
    assert first == replayed
    assert first.poll_count == 3
    assert first.end_cursor == 106
    assert first.checkpoint_ids == tuple(x.checkpoint_id for x in checkpoints)


def test_live_rpc_session_rejects_non_monotonic_slots() -> None:
    session = start_live_session("solana-production", 100)
    try:
        run_live_rpc_session(
            session, _fetcher_factory([101, 99]), start_cursor=100, max_polls=2
        )
    except ValueError:
        pass
    else:
        raise AssertionError("regressing slots must fail closed")


def test_retry_schedule_is_deterministic_backoff() -> None:
    schedule = build_retry_schedule(
        "solana-production", "getTransaction",
        ProviderRetryPolicy(max_retries=3, backoff_slots=5), base_slot=100,
    )
    assert tuple((x.attempt, x.scheduled_slot) for x in schedule.entries) == (
        (1, 105), (2, 110), (3, 115),
    )
    assert schedule == build_retry_schedule(
        "solana-production", "getTransaction",
        ProviderRetryPolicy(max_retries=3, backoff_slots=5), base_slot=100,
    )


def test_provider_health_monitor_thresholds() -> None:
    healthy = monitor_provider_health(
        "solana-production", observed_slot=200, success_count=19, failure_count=1
    )
    assert healthy.healthy
    assert healthy.availability_bps == 9500
    degraded = monitor_provider_health(
        "solana-production", observed_slot=200, success_count=8, failure_count=2
    )
    assert not degraded.healthy
    try:
        monitor_provider_health(
            "solana-production", observed_slot=200, success_count=0, failure_count=0
        )
    except ValueError:
        pass
    else:
        raise AssertionError("zero observations must fail closed")


def _payload(source_id: str, slot: int) -> EvidencePayload:
    return EvidencePayload(
        source_id=source_id,
        evidence_type="live_candidate",
        timestamp=slot,
        data={"candidate": {"slot": slot}},
        metadata={"authority": "NONE"},
    )


def test_live_ledger_commit_loop_is_deterministic() -> None:
    session = start_live_session("solana-production", 100)
    payloads = (_payload("live-a", 101), _payload("live-b", 102))
    ledger = _RecordingLedger()
    receipt = commit_live_payloads(session, payloads, ledger)
    assert receipt.commit_count == 2
    assert receipt.committed_ids == tuple(ledger.appended)
    assert receipt == commit_live_payloads(session, payloads, _RecordingLedger())


def test_live_candidate_refresh_and_deduplication() -> None:
    session = start_live_session("solana-production", 100)
    duplicate = _payload("live-a", 101)
    unique = deduplicate_live_candidates((duplicate, _payload("live-b", 102), duplicate))
    assert len(unique) == 2
    refresh = refresh_live_candidates(session, 102, unique)
    assert refresh.candidate_ids == tuple(
        sorted(item.get_canonical_id() for item in unique)
    )
    assert refresh == refresh_live_candidates(session, 102, unique)


def _failure_evidence(retry_count: int) -> LiveProviderFailureEvidence:
    return LiveProviderFailureEvidence(
        "solana-production",
        "getSlot",
        retry_count,
        deterministic_id(
            "live_provider_failure",
            {
                "operation": "getSlot",
                "provider_id": "solana-production",
                "retry_count": retry_count,
                "schema_version": "live_provider_failure.v1",
            },
        ),
    )


def test_live_dashboard_replay_recovery_and_readiness_gate() -> None:
    session = start_live_session("solana-production", 100)
    _, checkpoints = run_live_rpc_session(
        session, _fetcher_factory([101, 103, 106]), start_cursor=100, max_polls=3
    )
    candidates = (_payload("live-a", 101), _payload("live-b", 102))
    health = monitor_provider_health(
        "solana-production", observed_slot=106, success_count=19, failure_count=1
    )
    dashboard = refresh_live_dashboard(session, checkpoints, candidates, health)
    assert dashboard.refreshed_slot == 106
    assert dashboard.healthy

    replay = capture_live_replay(session, checkpoints)
    assert replay.checkpoint_ids == tuple(x.checkpoint_id for x in checkpoints)

    policy = ProviderRetryPolicy(max_retries=3, backoff_slots=5)
    recovery = recover_live_failure(session, _failure_evidence(2), checkpoints[-1], policy)
    assert recovery.recovered
    assert recovery.resume_slot == 111
    exhausted = recover_live_failure(session, _failure_evidence(4), checkpoints[-1], policy)
    assert not exhausted.recovered

    commit = commit_live_payloads(session, candidates, _RecordingLedger())
    gate = evaluate_operational_readiness(
        session, dashboard=dashboard, replay=replay, health=health, commit=commit
    )
    assert gate.ready
    assert gate.passed_checks == gate.checks
    assert gate == evaluate_operational_readiness(
        session, dashboard=dashboard, replay=replay, health=health, commit=commit
    )
