from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application.audit_recovery_gate import (
    AuditRecoveryGateDecision,
    AuditRecoveryGateStatus,
    FailClosedAuditRecoveryGate,
)
from smart_money.application.checkpointed_ingestion import (
    CheckpointedIngestionResult,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.market_identity import MarketId

_SCHEMA_VERSION = "recovery_gated_ingestion.v1"
_READY_STATUSES = frozenset(
    {
        AuditRecoveryGateStatus.READY_CURRENT,
        AuditRecoveryGateStatus.READY_ADVANCED,
    }
)


@runtime_checkable
class CheckpointedIngestionRunner(Protocol):
    async def run(
        self,
        market: MarketId,
        *,
        max_events: int | None = None,
    ) -> CheckpointedIngestionResult:
        """Run one checkpointed ingestion session."""
        ...


@dataclass(frozen=True, slots=True)
class RecoveryGatedIngestionResult:
    """Content-addressed linkage between recovery proof and ingestion result."""

    run_id: str
    gate_decision: AuditRecoveryGateDecision
    ingestion_result: CheckpointedIngestionResult
    requested_max_events: int | None
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        object.__setattr__(self, "run_id", self.run_id.strip())
        if not isinstance(self.gate_decision, AuditRecoveryGateDecision):
            raise TypeError(
                "gate_decision must be an AuditRecoveryGateDecision"
            )
        if (
            not self.gate_decision.allowed
            or self.gate_decision.status not in _READY_STATUSES
        ):
            raise ValueError("gate_decision must authorize ingestion")
        if not isinstance(self.ingestion_result, CheckpointedIngestionResult):
            raise TypeError(
                "ingestion_result must be a CheckpointedIngestionResult"
            )
        if self.requested_max_events is not None:
            if isinstance(
                self.requested_max_events,
                bool,
            ) or not isinstance(self.requested_max_events, int):
                raise TypeError(
                    "requested_max_events must be an integer or None"
                )
            if self.requested_max_events <= 0:
                raise ValueError("requested_max_events must be positive")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported recovery-gated ingestion schema_version"
            )
        expected_id = deterministic_id(
            "recovery_gated_ingestion",
            self.identity_payload(),
        )
        if self.run_id != expected_id:
            raise ValueError("run_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, object]:
        return {
            "gate_decision": self.gate_decision.canonical_dict(),
            "ingestion_result": self.ingestion_result.canonical_dict(),
            "requested_max_events": self.requested_max_events,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"run_id": self.run_id, **self.identity_payload()}

    @property
    def gate_decision_id(self) -> str:
        return self.gate_decision.decision_id

    @property
    def ingestion_session_id(self) -> str:
        return self.ingestion_result.session_id


@dataclass(frozen=True, slots=True)
class RecoveryGatedIngestionSession:
    gate: FailClosedAuditRecoveryGate
    session: CheckpointedIngestionRunner

    def __post_init__(self) -> None:
        if not isinstance(self.gate, FailClosedAuditRecoveryGate):
            raise TypeError("gate must be a FailClosedAuditRecoveryGate")
        if not isinstance(self.session, CheckpointedIngestionRunner):
            raise TypeError("session must satisfy CheckpointedIngestionRunner")

    async def run(
        self,
        market: MarketId,
        *,
        max_events: int | None = None,
        advance_if_required: bool = False,
    ) -> RecoveryGatedIngestionResult:
        self._validate_request(
            market=market,
            max_events=max_events,
            advance_if_required=advance_if_required,
        )

        async def run_session() -> CheckpointedIngestionResult:
            return await self.session.run(
                market,
                max_events=max_events,
            )

        gate_decision, ingestion_result = await self.gate.run_guarded(
            run_session,
            advance_if_required=advance_if_required,
        )
        if not isinstance(ingestion_result, CheckpointedIngestionResult):
            raise RuntimeError(
                "ingestion runner returned an invalid result type"
            )
        if ingestion_result.market_id != market.canonical_id:
            raise RuntimeError(
                "ingestion result market does not match requested market"
            )

        payload: dict[str, object] = {
            "gate_decision": gate_decision.canonical_dict(),
            "ingestion_result": ingestion_result.canonical_dict(),
            "requested_max_events": max_events,
            "schema_version": _SCHEMA_VERSION,
        }
        return RecoveryGatedIngestionResult(
            run_id=deterministic_id(
                "recovery_gated_ingestion",
                payload,
            ),
            gate_decision=gate_decision,
            ingestion_result=ingestion_result,
            requested_max_events=max_events,
        )

    @staticmethod
    def _validate_request(
        *,
        market: MarketId,
        max_events: int | None,
        advance_if_required: bool,
    ) -> None:
        if not isinstance(market, MarketId):
            raise TypeError("market must be a MarketId")
        if max_events is not None:
            if isinstance(max_events, bool) or not isinstance(max_events, int):
                raise TypeError("max_events must be an integer or None")
            if max_events <= 0:
                raise ValueError("max_events must be positive")
        if not isinstance(advance_if_required, bool):
            raise TypeError("advance_if_required must be a boolean")


__all__ = [
    "CheckpointedIngestionRunner",
    "RecoveryGatedIngestionResult",
    "RecoveryGatedIngestionSession",
]
