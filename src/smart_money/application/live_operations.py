from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from smart_money.application.live_discovery import (
    LiveDiscoveryReplaySession,
    LiveObservationCheckpoint,
    LiveProviderFailureEvidence,
    LiveProviderSession,
    ProviderRetryPolicy,
    checkpoint_session,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload


@dataclass(frozen=True, slots=True)
class LiveRpcSessionRunReceipt:
    session_id: str
    start_cursor: int
    end_cursor: int
    poll_count: int
    checkpoint_ids: tuple[str, ...]
    run_id: str
    schema_version: str = "live_rpc_session_run.v1"


def run_live_rpc_session(
    session: LiveProviderSession,
    fetcher: Callable[..., Mapping[str, Any]],
    *,
    start_cursor: int,
    max_polls: int,
) -> tuple[LiveRpcSessionRunReceipt, tuple[LiveObservationCheckpoint, ...]]:
    if not isinstance(session, LiveProviderSession):
        raise TypeError("session must be LiveProviderSession")
    if not callable(fetcher):
        raise TypeError("fetcher must be callable")
    for value, name in ((start_cursor, "start_cursor"), (max_polls, "max_polls")):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if max_polls == 0:
        raise ValueError("max_polls must be positive")

    cursor = start_cursor
    checkpoints: list[LiveObservationCheckpoint] = []
    for _ in range(max_polls):
        result = fetcher(
            "getSlot", {"commitment": "confirmed", "minContextSlot": cursor}
        )
        if not isinstance(result, Mapping) or "slot" not in result:
            raise ValueError("fetcher result must contain slot")
        slot = result["slot"]
        if isinstance(slot, bool) or not isinstance(slot, int) or slot < cursor:
            raise ValueError("slot must be a monotonic non-negative integer")
        cursor = slot
        checkpoints.append(checkpoint_session(session, slot))
    checkpoint_ids = tuple(item.checkpoint_id for item in checkpoints)
    identity = {
        "checkpoint_ids": checkpoint_ids,
        "end_cursor": cursor,
        "poll_count": len(checkpoints),
        "schema_version": "live_rpc_session_run.v1",
        "session_id": session.session_id,
        "start_cursor": start_cursor,
    }
    receipt = LiveRpcSessionRunReceipt(
        session.session_id, start_cursor, cursor, len(checkpoints), checkpoint_ids,
        deterministic_id("live-rpc-session-run", identity),
    )
    return receipt, tuple(checkpoints)


@dataclass(frozen=True, slots=True)
class RetryScheduleEntry:
    attempt: int
    scheduled_slot: int


@dataclass(frozen=True, slots=True)
class PersistentRetrySchedule:
    provider_id: str
    operation: str
    base_slot: int
    entries: tuple[RetryScheduleEntry, ...]
    schedule_id: str
    schema_version: str = "persistent_retry_schedule.v1"


def build_retry_schedule(
    provider_id: str,
    operation: str,
    policy: ProviderRetryPolicy,
    *,
    base_slot: int,
) -> PersistentRetrySchedule:
    for value, name in ((provider_id, "provider_id"), (operation, "operation")):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be non-empty")
    if not isinstance(policy, ProviderRetryPolicy):
        raise TypeError("policy must be ProviderRetryPolicy")
    if isinstance(base_slot, bool) or not isinstance(base_slot, int) or base_slot < 0:
        raise ValueError("base_slot must be a non-negative integer")
    entries = tuple(
        RetryScheduleEntry(attempt, base_slot + attempt * policy.backoff_slots)
        for attempt in range(1, policy.max_retries + 1)
    )
    identity = {
        "base_slot": base_slot,
        "backoff_slots": policy.backoff_slots,
        "max_retries": policy.max_retries,
        "operation": operation.strip(),
        "provider_id": provider_id.strip(),
        "schema_version": "persistent_retry_schedule.v1",
    }
    return PersistentRetrySchedule(
        provider_id.strip(), operation.strip(), base_slot, entries,
        deterministic_id("persistent-retry-schedule", identity),
    )


@dataclass(frozen=True, slots=True)
class ProviderHealthReport:
    provider_id: str
    observed_slot: int
    success_count: int
    failure_count: int
    availability_bps: int
    healthy: bool
    report_id: str
    schema_version: str = "provider_health_report.v1"


def monitor_provider_health(
    provider_id: str,
    *,
    observed_slot: int,
    success_count: int,
    failure_count: int,
    min_availability_bps: int = 9000,
) -> ProviderHealthReport:
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("provider_id must be non-empty")
    counters = (
        (observed_slot, "observed_slot"),
        (success_count, "success_count"),
        (failure_count, "failure_count"),
        (min_availability_bps, "min_availability_bps"),
    )
    for value, name in counters:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")
    if min_availability_bps > 10000:
        raise ValueError("min_availability_bps must be at most 10000")
    total = success_count + failure_count
    if total == 0:
        raise ValueError("health requires at least one observation")
    availability_bps = success_count * 10000 // total
    healthy = availability_bps >= min_availability_bps
    identity = {
        "availability_bps": availability_bps,
        "failure_count": failure_count,
        "healthy": healthy,
        "min_availability_bps": min_availability_bps,
        "observed_slot": observed_slot,
        "provider_id": provider_id.strip(),
        "schema_version": "provider_health_report.v1",
        "success_count": success_count,
    }
    return ProviderHealthReport(
        provider_id.strip(), observed_slot, success_count, failure_count,
        availability_bps, healthy,
        deterministic_id("provider-health-report", identity),
    )


@dataclass(frozen=True, slots=True)
class LiveLedgerCommitReceipt:
    session_id: str
    committed_ids: tuple[str, ...]
    commit_count: int
    commit_id: str
    schema_version: str = "live_ledger_commit.v1"


def commit_live_payloads(
    session: LiveProviderSession,
    payloads: tuple[EvidencePayload, ...],
    ledger: EvidenceLedger,
) -> LiveLedgerCommitReceipt:
    if not isinstance(session, LiveProviderSession):
        raise TypeError("session must be LiveProviderSession")
    if not isinstance(payloads, tuple) or not payloads:
        raise ValueError("payloads must be a non-empty tuple")
    if not all(isinstance(item, EvidencePayload) for item in payloads):
        raise TypeError("payloads must contain EvidencePayload values")
    committed: list[str] = []
    for payload in payloads:
        canonical_id = payload.get_canonical_id()
        if ledger.append(payload) != canonical_id:
            raise ValueError("ledger identity mismatch")
        committed.append(canonical_id)
    identity = {
        "committed_ids": tuple(committed),
        "schema_version": "live_ledger_commit.v1",
        "session_id": session.session_id,
    }
    return LiveLedgerCommitReceipt(
        session.session_id, tuple(committed), len(committed),
        deterministic_id("live-ledger-commit", identity),
    )


@dataclass(frozen=True, slots=True)
class LiveCandidateRefresh:
    session_id: str
    slot: int
    candidate_ids: tuple[str, ...]
    refresh_id: str
    schema_version: str = "live_candidate_refresh.v1"


def refresh_live_candidates(
    session: LiveProviderSession,
    slot: int,
    candidates: tuple[EvidencePayload, ...],
) -> LiveCandidateRefresh:
    if not isinstance(session, LiveProviderSession):
        raise TypeError("session must be LiveProviderSession")
    if isinstance(slot, bool) or not isinstance(slot, int) or slot < 0:
        raise ValueError("slot must be a non-negative integer")
    if not isinstance(candidates, tuple) or not all(
        isinstance(item, EvidencePayload) for item in candidates
    ):
        raise TypeError("candidates must be tuple of EvidencePayload")
    candidate_ids = tuple(sorted(item.get_canonical_id() for item in candidates))
    identity = {
        "candidate_ids": candidate_ids,
        "schema_version": "live_candidate_refresh.v1",
        "session_id": session.session_id,
        "slot": slot,
    }
    return LiveCandidateRefresh(
        session.session_id, slot, candidate_ids,
        deterministic_id("live-candidate-refresh", identity),
    )


def deduplicate_live_candidates(
    candidates: tuple[EvidencePayload, ...],
) -> tuple[EvidencePayload, ...]:
    if not isinstance(candidates, tuple) or not all(
        isinstance(item, EvidencePayload) for item in candidates
    ):
        raise TypeError("candidates must be tuple of EvidencePayload")
    unique: dict[str, EvidencePayload] = {}
    for item in candidates:
        unique.setdefault(item.get_canonical_id(), item)
    return tuple(unique[key] for key in sorted(unique))


@dataclass(frozen=True, slots=True)
class LiveDashboardSnapshot:
    session_id: str
    refreshed_slot: int
    checkpoint_count: int
    candidate_count: int
    healthy: bool
    snapshot_id: str
    schema_version: str = "live_dashboard_snapshot.v1"


def refresh_live_dashboard(
    session: LiveProviderSession,
    checkpoints: tuple[LiveObservationCheckpoint, ...],
    candidates: tuple[EvidencePayload, ...],
    health: ProviderHealthReport,
) -> LiveDashboardSnapshot:
    if not isinstance(session, LiveProviderSession):
        raise TypeError("session must be LiveProviderSession")
    if not isinstance(checkpoints, tuple) or not all(
        isinstance(item, LiveObservationCheckpoint) for item in checkpoints
    ):
        raise TypeError("checkpoints must be tuple of LiveObservationCheckpoint")
    if not isinstance(candidates, tuple) or not all(
        isinstance(item, EvidencePayload) for item in candidates
    ):
        raise TypeError("candidates must be tuple of EvidencePayload")
    if not isinstance(health, ProviderHealthReport):
        raise TypeError("health must be ProviderHealthReport")
    if any(item.session_id != session.session_id for item in checkpoints):
        raise ValueError("checkpoints must belong to the session")
    refreshed_slot = max(
        (item.slot for item in checkpoints), default=session.started_slot
    )
    identity = {
        "candidate_ids": tuple(sorted(x.get_canonical_id() for x in candidates)),
        "checkpoint_ids": tuple(x.checkpoint_id for x in checkpoints),
        "health_report_id": health.report_id,
        "refreshed_slot": refreshed_slot,
        "schema_version": "live_dashboard_snapshot.v1",
        "session_id": session.session_id,
    }
    return LiveDashboardSnapshot(
        session.session_id, refreshed_slot, len(checkpoints), len(candidates),
        health.healthy and bool(checkpoints),
        deterministic_id("live-dashboard-snapshot", identity),
    )


def capture_live_replay(
    session: LiveProviderSession,
    checkpoints: tuple[LiveObservationCheckpoint, ...],
) -> LiveDiscoveryReplaySession:
    if not isinstance(session, LiveProviderSession):
        raise TypeError("session must be LiveProviderSession")
    if not isinstance(checkpoints, tuple) or not checkpoints or not all(
        isinstance(item, LiveObservationCheckpoint) for item in checkpoints
    ):
        raise ValueError("checkpoints must be a non-empty tuple")
    if any(item.session_id != session.session_id for item in checkpoints):
        raise ValueError("checkpoints must belong to the session")
    slots = tuple(item.slot for item in checkpoints)
    if any(later < earlier for earlier, later in zip(slots, slots[1:])):
        raise ValueError("checkpoints must be slot-ordered")
    checkpoint_ids = tuple(item.checkpoint_id for item in checkpoints)
    return LiveDiscoveryReplaySession(
        session.session_id,
        checkpoint_ids,
        deterministic_id(
            "live_discovery_replay",
            {
                "checkpoint_ids": checkpoint_ids,
                "schema_version": "live_discovery_replay.v1",
                "session_id": session.session_id,
            },
        ),
    )


@dataclass(frozen=True, slots=True)
class LiveFailureRecoveryReceipt:
    session_id: str
    failure_evidence_id: str
    resume_slot: int
    recovered: bool
    recovery_id: str
    schema_version: str = "live_failure_recovery.v1"


def recover_live_failure(
    session: LiveProviderSession,
    failure: LiveProviderFailureEvidence,
    last_checkpoint: LiveObservationCheckpoint,
    policy: ProviderRetryPolicy,
) -> LiveFailureRecoveryReceipt:
    if not isinstance(session, LiveProviderSession):
        raise TypeError("session must be LiveProviderSession")
    if not isinstance(failure, LiveProviderFailureEvidence):
        raise TypeError("failure must be LiveProviderFailureEvidence")
    if not isinstance(last_checkpoint, LiveObservationCheckpoint):
        raise TypeError("last_checkpoint must be LiveObservationCheckpoint")
    if not isinstance(policy, ProviderRetryPolicy):
        raise TypeError("policy must be ProviderRetryPolicy")
    if last_checkpoint.session_id != session.session_id:
        raise ValueError("checkpoint must belong to the session")
    recovered = failure.retry_count <= policy.max_retries
    resume_slot = last_checkpoint.slot + policy.backoff_slots
    identity = {
        "failure_evidence_id": failure.evidence_id,
        "recovered": recovered,
        "resume_slot": resume_slot,
        "schema_version": "live_failure_recovery.v1",
        "session_id": session.session_id,
    }
    return LiveFailureRecoveryReceipt(
        session.session_id, failure.evidence_id, resume_slot, recovered,
        deterministic_id("live-failure-recovery", identity),
    )


@dataclass(frozen=True, slots=True)
class OperationalReadinessGate:
    session_id: str
    checks: tuple[str, ...]
    passed_checks: tuple[str, ...]
    ready: bool
    gate_id: str
    schema_version: str = "operational_readiness_gate.v1"


def evaluate_operational_readiness(
    session: LiveProviderSession,
    *,
    dashboard: LiveDashboardSnapshot,
    replay: LiveDiscoveryReplaySession,
    health: ProviderHealthReport,
    commit: LiveLedgerCommitReceipt,
) -> OperationalReadinessGate:
    if not isinstance(session, LiveProviderSession):
        raise TypeError("session must be LiveProviderSession")
    subjects = (
        (dashboard, LiveDashboardSnapshot, "dashboard"),
        (replay, LiveDiscoveryReplaySession, "replay"),
        (health, ProviderHealthReport, "health"),
        (commit, LiveLedgerCommitReceipt, "commit"),
    )
    for value, expected, name in subjects:
        if not isinstance(value, expected):
            raise TypeError(f"{name} has unexpected type")
    ids = (dashboard.session_id, replay.session_id, commit.session_id)
    if any(item != session.session_id for item in ids):
        raise ValueError("all inputs must belong to the session")
    checks = (
        "dashboard_healthy",
        "replay_captured",
        "provider_healthy",
        "ledger_committed",
    )
    passed = tuple(
        name
        for name, ok in zip(
            checks,
            (
                dashboard.healthy,
                bool(replay.checkpoint_ids),
                health.healthy,
                commit.commit_count > 0,
            ),
        )
        if ok
    )
    ready = passed == checks
    identity = {
        "checks": checks,
        "passed_checks": passed,
        "ready": ready,
        "schema_version": "operational_readiness_gate.v1",
        "session_id": session.session_id,
    }
    return OperationalReadinessGate(
        session.session_id, checks, passed, ready,
        deterministic_id("operational-readiness-gate", identity),
    )


__all__ = [
    "LiveRpcSessionRunReceipt",
    "run_live_rpc_session",
    "RetryScheduleEntry",
    "PersistentRetrySchedule",
    "build_retry_schedule",
    "ProviderHealthReport",
    "monitor_provider_health",
    "LiveLedgerCommitReceipt",
    "commit_live_payloads",
    "LiveCandidateRefresh",
    "refresh_live_candidates",
    "deduplicate_live_candidates",
    "LiveDashboardSnapshot",
    "refresh_live_dashboard",
    "capture_live_replay",
    "LiveFailureRecoveryReceipt",
    "recover_live_failure",
    "OperationalReadinessGate",
    "evaluate_operational_readiness",
]
