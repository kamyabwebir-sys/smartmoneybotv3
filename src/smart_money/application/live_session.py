"""
live_session.py — Live RPC Session contracts and runner.

Slice 1.50  : LiveRpcSession, RetryAttempt/RetrySchedule, ProviderHealthEvidence
E18.1       : ShutdownReason, SessionState, SessionReceipt,
              create_session / advance_session / shutdown_session
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Slice 1.50 — Core session identity
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LegacyLiveRpcSession:
    session_id: str
    provider_id: str
    start_slot: int
    schema_version: str = "1.0"


def _hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()


def build_session_id(provider_id: str, start_slot: int) -> str:
    return _hash({"provider_id": provider_id, "start_slot": start_slot})


def create_live_rpc_session(provider_id: str, start_slot: int) -> LegacyLiveRpcSession:
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("provider_id must be a non-empty string")
    if not isinstance(start_slot, int) or start_slot < 0:
        raise ValueError("start_slot must be a non-negative integer")
    return LegacyLiveRpcSession(
        session_id=build_session_id(provider_id, start_slot),
        provider_id=provider_id,
        start_slot=start_slot,
    )


# ---------------------------------------------------------------------------
# Slice 1.50 — Retry scheduling
# ---------------------------------------------------------------------------

class LegacyRetryAttempt:
    MAX_ATTEMPTS = 10

    def __init__(self, attempt_number: int, base_delay_ms: int = 500) -> None:
        if not isinstance(attempt_number, int) or attempt_number < 0:
            raise ValueError("attempt_number must be a non-negative integer")
        if not isinstance(base_delay_ms, int) or base_delay_ms <= 0:
            raise ValueError("base_delay_ms must be a positive integer")
        self.attempt_number = attempt_number
        self.base_delay_ms = base_delay_ms

    @property
    def delay_ms(self) -> int:
        return min(self.base_delay_ms * (2 ** self.attempt_number), 30_000)

    @property
    def is_exhausted(self) -> bool:
        return self.attempt_number >= self.MAX_ATTEMPTS


@dataclass(frozen=True)
class LegacyRetrySchedule:
    session_id: str
    max_attempts: int
    base_delay_ms: int
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        if self.base_delay_ms <= 0:
            raise ValueError("base_delay_ms must be positive")


# ---------------------------------------------------------------------------
# Slice 1.50 — Provider health evidence
# ---------------------------------------------------------------------------

class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class LegacyProviderHealthEvidence:
    evidence_id: str
    provider_id: str
    success_rate_bps: int
    status: str
    schema_version: str = "1.0"


def build_legacy_health_evidence(
    provider_id: str, success_rate_bps: int
) -> LegacyProviderHealthEvidence:
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("provider_id must be a non-empty string")
    if not isinstance(success_rate_bps, int) or not (0 <= success_rate_bps <= 10_000):
        raise ValueError("success_rate_bps must be an integer in [0, 10000]")

    if success_rate_bps >= 9_000:
        status = HealthStatus.HEALTHY.value
    elif success_rate_bps >= 5_000:
        status = HealthStatus.DEGRADED.value
    else:
        status = HealthStatus.UNAVAILABLE.value

    evidence_id = _hash(
        {"provider_id": provider_id, "success_rate_bps": success_rate_bps, "status": status}
    )
    return LegacyProviderHealthEvidence(
        evidence_id=evidence_id,
        provider_id=provider_id,
        success_rate_bps=success_rate_bps,
        status=status,
    )


# ---------------------------------------------------------------------------
# E18.1 — Live Session Runner contracts
# ---------------------------------------------------------------------------

class ShutdownReason(str, Enum):
    REQUESTED = "REQUESTED"
    ERROR = "ERROR"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    REPLAY_COMPLETE = "REPLAY_COMPLETE"
    GOVERNANCE_HALT = "GOVERNANCE_HALT"


@dataclass(frozen=True)
class SessionState:
    """Immutable snapshot of a live session at a point in time."""

    session_id: str
    provider_id: str
    start_slot: int
    current_slot: int
    cursor: str
    is_active: bool
    shutdown_reason: Optional[str]
    slots_processed: int
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id must be non-empty")
        if not self.provider_id:
            raise ValueError("provider_id must be non-empty")
        if self.start_slot < 0:
            raise ValueError("start_slot must be >= 0")
        if self.current_slot < self.start_slot:
            raise ValueError("current_slot must be >= start_slot")
        if self.slots_processed < 0:
            raise ValueError("slots_processed must be >= 0")
        if not self.is_active and self.shutdown_reason is None:
            raise ValueError("inactive session must have a shutdown_reason")


@dataclass(frozen=True)
class SessionReceipt:
    """Deterministic, immutable end-of-session receipt."""

    receipt_id: str
    session_id: str
    provider_id: str
    start_slot: int
    end_slot: int
    slots_processed: int
    shutdown_reason: str
    schema_version: str = "1.0"


LegacySessionState = SessionState


def _receipt_id(session_id: str, end_slot: int, shutdown_reason: str) -> str:
    return _hash(
        {"session_id": session_id, "end_slot": end_slot, "shutdown_reason": shutdown_reason}
    )


def create_session(
    provider_id: str, start_slot: int, initial_cursor: str
) -> LegacySessionState:
    """Create a fresh active SessionState."""
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("provider_id must be a non-empty string")
    if not isinstance(start_slot, int) or start_slot < 0:
        raise ValueError("start_slot must be a non-negative integer")
    if not isinstance(initial_cursor, str):
        raise TypeError("initial_cursor must be a string")

    return LegacySessionState(
        session_id=build_session_id(provider_id, start_slot),
        provider_id=provider_id,
        start_slot=start_slot,
        current_slot=start_slot,
        cursor=initial_cursor,
        is_active=True,
        shutdown_reason=None,
        slots_processed=0,
    )


def advance_session(
    state: LegacySessionState, new_slot: int, new_cursor: str
) -> LegacySessionState:
    """Return a new SessionState advanced to new_slot."""
    if not isinstance(state, LegacySessionState):
        raise TypeError("state must be a SessionState")
    if not state.is_active:
        raise ValueError("cannot advance an inactive session")
    if not isinstance(new_slot, int) or new_slot < state.current_slot:
        raise ValueError(
            f"new_slot must be >= current_slot ({state.current_slot})"
        )
    if not isinstance(new_cursor, str):
        raise TypeError("new_cursor must be a string")

    slots_delta = new_slot - state.current_slot
    return LegacySessionState(
        session_id=state.session_id,
        provider_id=state.provider_id,
        start_slot=state.start_slot,
        current_slot=new_slot,
        cursor=new_cursor,
        is_active=True,
        shutdown_reason=None,
        slots_processed=state.slots_processed + slots_delta,
    )


def shutdown_session(
    state: LegacySessionState, reason: ShutdownReason
) -> tuple[LegacySessionState, SessionReceipt]:
    """Shut down an active session; return (final_state, receipt)."""
    if not isinstance(state, LegacySessionState):
        raise TypeError("state must be a SessionState")
    if not isinstance(reason, ShutdownReason):
        raise TypeError("reason must be a ShutdownReason")
    if not state.is_active:
        raise ValueError("session is already inactive")

    final_state = LegacySessionState(
        session_id=state.session_id,
        provider_id=state.provider_id,
        start_slot=state.start_slot,
        current_slot=state.current_slot,
        cursor=state.cursor,
        is_active=False,
        shutdown_reason=reason.value,
        slots_processed=state.slots_processed,
    )
    receipt = SessionReceipt(
        receipt_id=_receipt_id(state.session_id, state.current_slot, reason.value),
        session_id=state.session_id,
        provider_id=state.provider_id,
        start_slot=state.start_slot,
        end_slot=state.current_slot,
        slots_processed=state.slots_processed,
        shutdown_reason=reason.value,
    )
    return final_state, receipt


class SessionState(str, Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


@dataclass(frozen=True, slots=True)
class LiveRpcSession:
    session_id: str
    provider_id: str
    start_slot: int
    cursor: str
    state: SessionState = SessionState.RUNNING
    schema_version: str = "live_rpc_session.v1"


def create_live_session(
    provider_id: str, start_slot: int, cursor: str
) -> LiveRpcSession:
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("provider_id must be a non-empty string")
    if isinstance(start_slot, bool) or not isinstance(start_slot, int) or start_slot < 0:
        raise ValueError("start_slot must be a non-negative integer")
    if not isinstance(cursor, str) or not cursor.strip():
        raise ValueError("cursor must be a non-empty string")
    identity = {
        "cursor": cursor.strip(),
        "provider_id": provider_id.strip(),
        "schema_version": "live_rpc_session.v1",
        "start_slot": start_slot,
    }
    return LiveRpcSession(
        _hash(identity)[:32], provider_id.strip(), start_slot, cursor.strip()
    )


class RetryErrorType(str, Enum):
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    PROVIDER_ERROR = "PROVIDER_ERROR"


@dataclass(frozen=True, slots=True)
class RetryAttempt:
    session_id: str
    attempt_number: int
    error_type: RetryErrorType
    base_delay_ms: int
    max_delay_ms: int
    attempt_id: str

    @property
    def delay_ms(self) -> int:
        return min(
            self.base_delay_ms * (2 ** (self.attempt_number - 1)),
            self.max_delay_ms,
        )


def build_retry_attempt(
    session_id: str,
    attempt_number: int,
    error_type: RetryErrorType,
    base_delay_ms: int = 500,
    max_delay_ms: int = 30_000,
) -> RetryAttempt:
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id must be non-empty")
    if isinstance(attempt_number, bool) or not isinstance(attempt_number, int) or attempt_number < 1:
        raise ValueError("attempt_number must be positive")
    if not isinstance(error_type, RetryErrorType):
        raise TypeError("error_type must be RetryErrorType")
    if base_delay_ms <= 0 or max_delay_ms < base_delay_ms:
        raise ValueError("invalid retry delay")
    identity = {
        "attempt_number": attempt_number,
        "base_delay_ms": base_delay_ms,
        "error_type": error_type.value,
        "max_delay_ms": max_delay_ms,
        "session_id": session_id.strip(),
    }
    return RetryAttempt(
        session_id.strip(), attempt_number, error_type, base_delay_ms,
        max_delay_ms, _hash(identity),
    )


@dataclass(frozen=True, slots=True)
class RetrySchedule:
    session_id: str
    max_attempts: int
    base_delay_ms: int
    max_delay_ms: int
    schedule_id: str


def build_retry_schedule(
    session_id: str,
    max_attempts: int = 3,
    base_delay_ms: int = 500,
    max_delay_ms: int = 30_000,
) -> RetrySchedule:
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id must be non-empty")
    if max_attempts <= 0 or base_delay_ms <= 0 or max_delay_ms < base_delay_ms:
        raise ValueError("invalid retry schedule")
    identity = {
        "base_delay_ms": base_delay_ms,
        "max_attempts": max_attempts,
        "max_delay_ms": max_delay_ms,
        "session_id": session_id.strip(),
    }
    return RetrySchedule(
        session_id.strip(), max_attempts, base_delay_ms, max_delay_ms,
        _hash(identity),
    )


@dataclass(frozen=True, slots=True)
class ProviderHealthEvidence:
    provider_id: str
    latency_ms: int
    success_rate_bps: int
    error_rate_bps: int
    slot_lag: int
    freshness_seconds: int
    status: HealthStatus
    health_id: str


def build_health_evidence(
    provider_id: str,
    latency_ms: int,
    success_rate_bps: int,
    error_rate_bps: int,
    slot_lag: int,
    freshness_seconds: int,
) -> ProviderHealthEvidence:
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("provider_id must be non-empty")
    values = (latency_ms, success_rate_bps, error_rate_bps, slot_lag, freshness_seconds)
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in values):
        raise ValueError("health metrics must be non-negative integers")
    if success_rate_bps > 10000 or error_rate_bps > 10000:
        raise ValueError("rates must be at most 10000")
    status = (
        HealthStatus.HEALTHY
        if success_rate_bps >= 9000
        else HealthStatus.DEGRADED
        if success_rate_bps >= 5000
        else HealthStatus.UNAVAILABLE
    )
    identity = {
        "error_rate_bps": error_rate_bps,
        "freshness_seconds": freshness_seconds,
        "latency_ms": latency_ms,
        "provider_id": provider_id.strip(),
        "slot_lag": slot_lag,
        "status": status.value,
        "success_rate_bps": success_rate_bps,
    }
    return ProviderHealthEvidence(
        provider_id.strip(), latency_ms, success_rate_bps, error_rate_bps,
        slot_lag, freshness_seconds, status, _hash(identity),
    )
