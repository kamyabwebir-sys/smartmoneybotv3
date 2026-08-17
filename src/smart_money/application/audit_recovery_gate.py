from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from smart_money.application.trusted_audit_head import (
    PrefixVerifiableHistoricalAuditStore,
    TrustedAuditHead,
    TrustedAuditHeadStatus,
    TrustedAuditHeadStore,
    TrustedAuditHeadVerification,
    advance_trusted_audit_head,
    make_trusted_audit_head,
    verify_trusted_audit_head,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "audit_recovery_gate.v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_ResultT = TypeVar("_ResultT")


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _require_sha256(value: object, field_name: str) -> str:
    digest = _require_text(value, field_name)
    if _SHA256_PATTERN.fullmatch(digest) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")
    return digest


def _require_count(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


class AuditRecoveryGateStatus(str, Enum):
    READY_CURRENT = "READY_CURRENT"
    READY_ADVANCED = "READY_ADVANCED"
    BLOCKED_MISSING_HEAD = "BLOCKED_MISSING_HEAD"
    BLOCKED_ADVANCE_REQUIRED = "BLOCKED_ADVANCE_REQUIRED"
    BLOCKED_ROLLBACK = "BLOCKED_ROLLBACK"
    BLOCKED_DIVERGED = "BLOCKED_DIVERGED"


_ALLOWED_STATUSES = frozenset(
    {
        AuditRecoveryGateStatus.READY_CURRENT,
        AuditRecoveryGateStatus.READY_ADVANCED,
    }
)


@dataclass(frozen=True, slots=True)
class AuditRecoveryGateDecision:
    """Deterministic receipt proving whether guarded work may start."""

    decision_id: str
    status: AuditRecoveryGateStatus
    allowed: bool
    advance_requested: bool
    trusted_anchor_id: str | None
    verification_id: str | None
    manifest_store_hash: str
    manifest_count: int
    latest_audit_id: str | None
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "decision_id",
            _require_text(self.decision_id, "decision_id"),
        )
        if not isinstance(self.status, AuditRecoveryGateStatus):
            raise TypeError("status must be an AuditRecoveryGateStatus")
        for field_name in ("allowed", "advance_requested"):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be a boolean")
        if self.allowed != (self.status in _ALLOWED_STATUSES):
            raise ValueError("allowed must agree with gate status")
        for field_name in ("trusted_anchor_id", "verification_id"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _require_text(value, field_name),
                )
        if self.allowed and (
            self.trusted_anchor_id is None or self.verification_id is None
        ):
            raise ValueError("allowed decision requires anchor and verification")
        object.__setattr__(
            self,
            "manifest_store_hash",
            _require_sha256(
                self.manifest_store_hash,
                "manifest_store_hash",
            ),
        )
        object.__setattr__(
            self,
            "manifest_count",
            _require_count(self.manifest_count, "manifest_count"),
        )
        if self.latest_audit_id is not None:
            object.__setattr__(
                self,
                "latest_audit_id",
                _require_text(self.latest_audit_id, "latest_audit_id"),
            )
        if (self.manifest_count == 0) != (self.latest_audit_id is None):
            raise ValueError(
                "latest_audit_id presence must agree with manifest_count"
            )
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported audit recovery gate schema_version")
        expected_id = deterministic_id(
            "audit_recovery_gate",
            self.identity_payload(),
        )
        if self.decision_id != expected_id:
            raise ValueError("decision_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, object]:
        return {
            "advance_requested": self.advance_requested,
            "allowed": self.allowed,
            "latest_audit_id": self.latest_audit_id,
            "manifest_count": self.manifest_count,
            "manifest_store_hash": self.manifest_store_hash,
            "schema_version": self.schema_version,
            "status": self.status.value,
            "trusted_anchor_id": self.trusted_anchor_id,
            "verification_id": self.verification_id,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"decision_id": self.decision_id, **self.identity_payload()}


class AuditRecoveryGateBlockedError(RuntimeError):
    def __init__(self, decision: AuditRecoveryGateDecision) -> None:
        self.decision = decision
        super().__init__(
            f"audit recovery gate blocked execution: {decision.status.value}"
        )


def _make_decision(
    *,
    status: AuditRecoveryGateStatus,
    advance_requested: bool,
    head: TrustedAuditHead | None,
    verification: TrustedAuditHeadVerification | None,
    manifest_store_hash: str,
    manifest_count: int,
    latest_audit_id: str | None,
) -> AuditRecoveryGateDecision:
    allowed = status in _ALLOWED_STATUSES
    payload: dict[str, object] = {
        "advance_requested": advance_requested,
        "allowed": allowed,
        "latest_audit_id": latest_audit_id,
        "manifest_count": manifest_count,
        "manifest_store_hash": manifest_store_hash,
        "schema_version": _SCHEMA_VERSION,
        "status": status.value,
        "trusted_anchor_id": None if head is None else head.anchor_id,
        "verification_id": (
            None if verification is None else verification.verification_id
        ),
    }
    return AuditRecoveryGateDecision(
        decision_id=deterministic_id("audit_recovery_gate", payload),
        status=status,
        allowed=allowed,
        advance_requested=advance_requested,
        trusted_anchor_id=payload["trusted_anchor_id"],  # type: ignore[arg-type]
        verification_id=payload["verification_id"],  # type: ignore[arg-type]
        manifest_store_hash=manifest_store_hash,
        manifest_count=manifest_count,
        latest_audit_id=latest_audit_id,
    )


@dataclass(frozen=True, slots=True)
class FailClosedAuditRecoveryGate:
    manifest_store: PrefixVerifiableHistoricalAuditStore
    head_store: TrustedAuditHeadStore

    def __post_init__(self) -> None:
        if not isinstance(
            self.manifest_store,
            PrefixVerifiableHistoricalAuditStore,
        ):
            raise TypeError("manifest_store must support prefix verification")
        if not isinstance(self.head_store, TrustedAuditHeadStore):
            raise TypeError("head_store must satisfy TrustedAuditHeadStore")

    def evaluate(
        self,
        *,
        advance_if_required: bool = False,
    ) -> AuditRecoveryGateDecision:
        if not isinstance(advance_if_required, bool):
            raise TypeError("advance_if_required must be a boolean")
        try:
            head = self.head_store.load()
        except FileNotFoundError:
            candidate = make_trusted_audit_head(
                manifest_store=self.manifest_store
            )
            if not advance_if_required:
                return _make_decision(
                    status=AuditRecoveryGateStatus.BLOCKED_MISSING_HEAD,
                    advance_requested=False,
                    head=None,
                    verification=None,
                    manifest_store_hash=candidate.manifest_store_hash,
                    manifest_count=candidate.manifest_count,
                    latest_audit_id=candidate.latest_audit_id,
                )
            return self._advance_decision(advance_requested=True)

        verification = verify_trusted_audit_head(
            head=head,
            manifest_store=self.manifest_store,
        )
        if verification.status is TrustedAuditHeadStatus.CURRENT:
            status = AuditRecoveryGateStatus.READY_CURRENT
        elif verification.status is TrustedAuditHeadStatus.ADVANCE_REQUIRED:
            if advance_if_required:
                return self._advance_decision(advance_requested=True)
            status = AuditRecoveryGateStatus.BLOCKED_ADVANCE_REQUIRED
        elif verification.status is TrustedAuditHeadStatus.ROLLBACK:
            status = AuditRecoveryGateStatus.BLOCKED_ROLLBACK
        else:
            status = AuditRecoveryGateStatus.BLOCKED_DIVERGED
        return _make_decision(
            status=status,
            advance_requested=advance_if_required,
            head=head,
            verification=verification,
            manifest_store_hash=verification.current_store_hash,
            manifest_count=verification.current_manifest_count,
            latest_audit_id=verification.current_latest_audit_id,
        )

    def open_or_raise(
        self,
        *,
        advance_if_required: bool = False,
    ) -> AuditRecoveryGateDecision:
        decision = self.evaluate(
            advance_if_required=advance_if_required,
        )
        if not decision.allowed:
            raise AuditRecoveryGateBlockedError(decision)
        return decision

    async def run_guarded(
        self,
        operation: Callable[[], Awaitable[_ResultT]],
        *,
        advance_if_required: bool = False,
    ) -> tuple[AuditRecoveryGateDecision, _ResultT]:
        if not callable(operation):
            raise TypeError("operation must be callable")
        decision = self.open_or_raise(
            advance_if_required=advance_if_required,
        )
        result = await operation()
        return decision, result

    def _advance_decision(
        self,
        *,
        advance_requested: bool,
    ) -> AuditRecoveryGateDecision:
        head = advance_trusted_audit_head(
            manifest_store=self.manifest_store,
            head_store=self.head_store,
        )
        verification = verify_trusted_audit_head(
            head=head,
            manifest_store=self.manifest_store,
        )
        if verification.status is not TrustedAuditHeadStatus.CURRENT:
            raise RuntimeError("advanced trusted audit head is not current")
        return _make_decision(
            status=AuditRecoveryGateStatus.READY_ADVANCED,
            advance_requested=advance_requested,
            head=head,
            verification=verification,
            manifest_store_hash=verification.current_store_hash,
            manifest_count=verification.current_manifest_count,
            latest_audit_id=verification.current_latest_audit_id,
        )


__all__ = [
    "AuditRecoveryGateBlockedError",
    "AuditRecoveryGateDecision",
    "AuditRecoveryGateStatus",
    "FailClosedAuditRecoveryGate",
]
