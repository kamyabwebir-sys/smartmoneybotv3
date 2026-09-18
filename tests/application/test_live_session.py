"""
E18.1 / E18.2 / E18.3 -- Live Session scaffold tests.
Deterministic, replayable, fail-closed. Zero I/O, zero wall-clock.
"""
from __future__ import annotations

import pytest

from smart_money.application.live_session import (
    SessionState,
    LiveRpcSession,
    create_live_session,
    RetryErrorType,
    RetryAttempt,
    RetrySchedule,
    build_retry_attempt,
    build_retry_schedule,
    HealthStatus,
    ProviderHealthEvidence,
    build_health_evidence,
)


def _session(**kw) -> LiveRpcSession:
    defaults = dict(provider_id="rpc-001", start_slot=100, cursor="slot:100")
    defaults.update(kw)
    return create_live_session(**defaults)


def _attempt(**kw) -> RetryAttempt:
    defaults = dict(
        session_id="sess-001",
        attempt_number=1,
        error_type=RetryErrorType.TIMEOUT,
    )
    defaults.update(kw)
    return build_retry_attempt(**defaults)


def _schedule(**kw) -> RetrySchedule:
    defaults = dict(session_id="sess-001")
    defaults.update(kw)
    return build_retry_schedule(**defaults)


def _health(**kw) -> ProviderHealthEvidence:
    defaults = dict(
        provider_id="rpc-001",
        latency_ms=50,
        success_rate_bps=9_500,
        error_rate_bps=500,
        slot_lag=3,
        freshness_seconds=5,
    )
    defaults.update(kw)
    return build_health_evidence(**defaults)


class TestLiveRpcSession:
    def test_deterministic_session_id(self) -> None:
        s1 = _session()
        s2 = _session()
        assert s1.session_id == s2.session_id
        assert len(s1.session_id) == 32

    def test_distinct_providers_produce_distinct_ids(self) -> None:
        a = _session(provider_id="rpc-001").session_id
        b = _session(provider_id="rpc-002").session_id
        assert a != b

    def test_default_state_is_running(self) -> None:
        assert _session().state == SessionState.RUNNING

    def test_fail_closed_empty_provider_id(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            create_live_session(provider_id="", start_slot=1, cursor="slot:1")

    def test_fail_closed_empty_cursor(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            create_live_session(provider_id="rpc-001", start_slot=1, cursor="")

    def test_fail_closed_negative_start_slot(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            create_live_session(provider_id="rpc-001", start_slot=-1, cursor="slot:-1")

    def test_replayable_across_instances(self) -> None:
        a = _session(provider_id="rpc-X", start_slot=42, cursor="slot:42")
        b = _session(provider_id="rpc-X", start_slot=42, cursor="slot:42")
        assert a.session_id == b.session_id

    def test_frozen_dataclass(self) -> None:
        s = _session()
        with pytest.raises((AttributeError, TypeError)):
            s.provider_id = "mutated"  # type: ignore[misc]


class TestRetryAttempt:
    def test_deterministic_attempt_id(self) -> None:
        assert _attempt().attempt_id == _attempt().attempt_id

    def test_exponential_backoff_attempt_2(self) -> None:
        a = _attempt(attempt_number=2, base_delay_ms=1_000, max_delay_ms=60_000)
        assert a.delay_ms == 2_000

    def test_exponential_backoff_capped(self) -> None:
        a = _attempt(attempt_number=10, base_delay_ms=1_000, max_delay_ms=5_000)
        assert a.delay_ms == 5_000

    def test_fail_closed_attempt_number_zero(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            build_retry_attempt(
                session_id="s",
                attempt_number=0,
                error_type=RetryErrorType.TIMEOUT,
            )

    def test_fail_closed_empty_session_id(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            build_retry_attempt(
                session_id="",
                attempt_number=1,
                error_type=RetryErrorType.TIMEOUT,
            )

    def test_fail_closed_negative_base_delay(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            build_retry_attempt(
                session_id="s",
                attempt_number=1,
                error_type=RetryErrorType.TIMEOUT,
                base_delay_ms=-1,
            )


class TestRetrySchedule:
    def test_deterministic_schedule_id(self) -> None:
        assert _schedule().schedule_id == _schedule().schedule_id

    def test_fail_closed_max_attempts_zero(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            build_retry_schedule(session_id="s", max_attempts=0)

    def test_fail_closed_max_delay_lt_base(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            build_retry_schedule(session_id="s", base_delay_ms=5_000, max_delay_ms=1_000)

    def test_replayable(self) -> None:
        a = _schedule(session_id="sess-replay", max_attempts=3)
        b = _schedule(session_id="sess-replay", max_attempts=3)
        assert a.schedule_id == b.schedule_id


class TestProviderHealthEvidence:
    def test_healthy_status(self) -> None:
        assert _health(success_rate_bps=9_500).status == HealthStatus.HEALTHY

    def test_degraded_status(self) -> None:
        assert _health(success_rate_bps=7_000).status == HealthStatus.DEGRADED

    def test_unavailable_status(self) -> None:
        assert _health(success_rate_bps=1_000).status == HealthStatus.UNAVAILABLE

    def test_deterministic_health_id(self) -> None:
        assert _health().health_id == _health().health_id

    def test_distinct_providers_distinct_ids(self) -> None:
        assert _health(provider_id="p1").health_id != _health(provider_id="p2").health_id

    def test_fail_closed_empty_provider_id(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            build_health_evidence(
                provider_id="",
                latency_ms=50,
                success_rate_bps=9_000,
                error_rate_bps=1_000,
                slot_lag=3,
                freshness_seconds=5,
            )

    def test_fail_closed_negative_latency(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            build_health_evidence(
                provider_id="rpc-001",
                latency_ms=-1,
                success_rate_bps=9_000,
                error_rate_bps=1_000,
                slot_lag=3,
                freshness_seconds=5,
            )

    def test_fail_closed_success_rate_out_of_range(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            build_health_evidence(
                provider_id="rpc-001",
                latency_ms=50,
                success_rate_bps=10_001,
                error_rate_bps=0,
                slot_lag=3,
                freshness_seconds=5,
            )

    def test_replayable_across_instances(self) -> None:
        kw = dict(
            provider_id="rpc-replay",
            latency_ms=100,
            success_rate_bps=9_200,
            error_rate_bps=800,
            slot_lag=5,
            freshness_seconds=10,
        )
        h1 = build_health_evidence(**kw)
        h2 = build_health_evidence(**kw)
        assert h1.health_id == h2.health_id