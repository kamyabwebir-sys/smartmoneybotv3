from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_chain_replay_verifier as chain_replay_model,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_recovery_replay_verifier as recovery_replay_model,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_gate import (
    DashboardSessionFinalRecoveryGateAuditRecoveryGate,
    DashboardSessionFinalRecoveryGateAuditRecoveryReceipt,
)
from smart_money.core.ids import deterministic_id


@runtime_checkable
class DashboardSessionFinalRecoveryGateAuditChainReplayReceiptStore(Protocol):
    def get(
        self, verification_id: str
    ) -> chain_replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayReceipt | None:
        ...


@runtime_checkable
class DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceiptStore(Protocol):
    def get(
        self, verification_id: str
    ) -> recovery_replay_model.DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt | None:
        ...


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt:
    expected_chain_id: str
    expected_chain_hash: str
    recovery_gate_chain_id: str | None
    chain_replay_verification_id: str
    persisted_chain_replay_verification_id: str | None
    recovery_replay_verification_id: str
    persisted_recovery_replay_verification_id: str | None
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = (
        "dashboard_session_final_recovery_gate_audit_recovery_full_audit.v1"
    )

    def __post_init__(self) -> None:
        if not isinstance(self.expected_chain_id, str) or not self.expected_chain_id.strip():
            raise ValueError("expected_chain_id must be non-empty")
        if (
            not isinstance(self.expected_chain_hash, str)
            or not self.expected_chain_hash.strip()
        ):
            raise ValueError("expected_chain_hash must be non-empty")
        if len(self.expected_chain_hash) != 64:
            raise ValueError("expected_chain_hash must be a SHA-256 hex digest")

        for name in (
            "recovery_gate_chain_id",
            "chain_replay_verification_id",
            "recovery_replay_verification_id",
        ):
            value = getattr(self, name)
            if name == "recovery_gate_chain_id":
                if value is not None and (
                    not isinstance(value, str) or not value.strip()
                ):
                    raise ValueError(
                        "recovery_gate_chain_id must be a non-empty string or None"
                    )
            elif not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        for name in (
            "persisted_chain_replay_verification_id",
            "persisted_recovery_replay_verification_id",
        ):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"{name} must be a non-empty string or None")

        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if not isinstance(self.mismatches, tuple) or not all(
            isinstance(item, str) and item.strip() for item in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if self.matches and self.mismatches:
            raise ValueError("matching full audit cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching full audit requires mismatches")
        if (
            self.schema_version
            != "dashboard_session_final_recovery_gate_audit_recovery_full_audit.v1"
        ):
            raise ValueError(
                "unsupported full recovery gate audit recovery schema_version"
            )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "expected_chain_id": self.expected_chain_id,
            "expected_chain_hash": self.expected_chain_hash,
            "recovery_gate_chain_id": self.recovery_gate_chain_id,
            "chain_replay_verification_id": self.chain_replay_verification_id,
            "persisted_chain_replay_verification_id": (
                self.persisted_chain_replay_verification_id
            ),
            "recovery_replay_verification_id": self.recovery_replay_verification_id,
            "persisted_recovery_replay_verification_id": (
                self.persisted_recovery_replay_verification_id
            ),
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def full_audit_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_recovery_gate_audit_recovery_full_audit",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier:
    gate: DashboardSessionFinalRecoveryGateAuditRecoveryGate = (
        DashboardSessionFinalRecoveryGateAuditRecoveryGate()
    )
    chain_replay_store: (
        DashboardSessionFinalRecoveryGateAuditChainReplayReceiptStore | None
    ) = None
    recovery_replay_store: (
        DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceiptStore | None
    ) = None

    def verify(
        self,
        chain: DashboardSessionFinalRecoveryGateAuditChain,
        chain_replay: chain_replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayReceipt,
        expected_recovery_receipt: DashboardSessionFinalRecoveryGateAuditRecoveryReceipt,
        recovery_replay: (
            recovery_replay_model.DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt
        ),
    ) -> DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt:
        if not isinstance(chain, DashboardSessionFinalRecoveryGateAuditChain):
            raise TypeError(
                "chain must be a DashboardSessionFinalRecoveryGateAuditChain"
            )
        if not isinstance(
            chain_replay,
            chain_replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayReceipt,
        ):
            raise TypeError(
                "chain_replay must be a "
                "DashboardSessionFinalRecoveryGateAuditChainReplayReceipt"
            )
        if not isinstance(
            expected_recovery_receipt,
            DashboardSessionFinalRecoveryGateAuditRecoveryReceipt,
        ):
            raise TypeError(
                "expected_recovery_receipt must be a "
                "DashboardSessionFinalRecoveryGateAuditRecoveryReceipt"
            )
        if not isinstance(
            recovery_replay,
            recovery_replay_model.DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt,
        ):
            raise TypeError(
                "recovery_replay must be a "
                "DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt"
            )

        _ = self.gate.evaluate(chain, chain_replay, recovery_replay)

        mismatches = tuple(
            field
            for field in (
                "recovery_gate_chain_id",
                "chain_replay_link",
                "chain_replay_hash_alignment",
                "chain_replay_verification_id_match",
                "recovery_chain_id_link",
                "recovery_replay_verification_id_link",
                "persisted_chain_replay",
                "persisted_recovery_replay",
            )
            if self._field_mismatch(
                field,
                chain,
                chain_replay,
                expected_recovery_receipt,
                recovery_replay,
            )
        )

        if self.chain_replay_store is not None:
            persisted_chain_replay = self.chain_replay_store.get(
                chain_replay.verification_id
            )
            if persisted_chain_replay is None:
                mismatches += ("persisted_gate_audit_chain_replay_missing",)
                persisted_chain_replay_id = None
            elif persisted_chain_replay != chain_replay:
                mismatches += ("persisted_gate_audit_chain_replay_mismatch",)
                persisted_chain_replay_id = persisted_chain_replay.verification_id
            else:
                persisted_chain_replay_id = persisted_chain_replay.verification_id
        else:
            mismatches += ("persisted_gate_audit_chain_replay_store_missing",)
            persisted_chain_replay_id = None

        if self.recovery_replay_store is not None:
            persisted_recovery_replay = self.recovery_replay_store.get(
                recovery_replay.verification_id
            )
            if persisted_recovery_replay is None:
                mismatches += ("persisted_gate_audit_recovery_replay_missing",)
                persisted_recovery_replay_id = None
            elif persisted_recovery_replay != recovery_replay:
                mismatches += ("persisted_gate_audit_recovery_replay_mismatch",)
                persisted_recovery_replay_id = persisted_recovery_replay.verification_id
            else:
                persisted_recovery_replay_id = persisted_recovery_replay.verification_id
        else:
            mismatches += ("persisted_gate_audit_recovery_replay_store_missing",)
            persisted_recovery_replay_id = None

        return DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt(
            expected_chain_id=chain.chain_id,
            expected_chain_hash=chain.chain_hash,
            recovery_gate_chain_id=expected_recovery_receipt.chain_id,
            chain_replay_verification_id=chain_replay.verification_id,
            persisted_chain_replay_verification_id=persisted_chain_replay_id,
            recovery_replay_verification_id=recovery_replay.verification_id,
            persisted_recovery_replay_verification_id=persisted_recovery_replay_id,
            matches=not mismatches,
            mismatches=mismatches,
        )

    def _field_mismatch(
        self,
        field: str,
        chain: DashboardSessionFinalRecoveryGateAuditChain,
        chain_replay: chain_replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayReceipt,
        expected_recovery_receipt: DashboardSessionFinalRecoveryGateAuditRecoveryReceipt,
        recovery_replay: (
            recovery_replay_model.DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt
        ),
    ) -> bool:
        if field == "recovery_gate_chain_id":
            return (
                expected_recovery_receipt.chain_id != chain.chain_id
                or expected_recovery_receipt.decision != "READY"
            )
        if field == "chain_replay_link":
            return (
                chain_replay.expected_chain_id != chain.chain_id
                or chain_replay.actual_chain_id != chain.chain_id
            )
        if field == "chain_replay_hash_alignment":
            return chain_replay.expected_chain_hash != chain.chain_hash
        if field == "chain_replay_verification_id_match":
            return (
                chain_replay.verification_id
                != expected_recovery_receipt.replay_verification_id
            )
        if field == "recovery_chain_id_link":
            return expected_recovery_receipt.decision != "READY" or (
                expected_recovery_receipt.chain_id != chain.chain_id
            )
        if field == "recovery_replay_verification_id_link":
            return (
                recovery_replay.expected_receipt_id
                != expected_recovery_receipt.receipt_id
            )
        return False


__all__ = [
    "DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt",
    "DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier",
    "DashboardSessionFinalRecoveryGateAuditChainReplayReceiptStore",
    "DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceiptStore",
]
