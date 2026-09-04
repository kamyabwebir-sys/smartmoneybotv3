from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_cohort_ledger import WalletCohortLedgerReceipt
from smart_money.application.wallet_cohort_replay import WalletCohortReplayReceipt
from smart_money.application.wallet_cohort_replay_store_verifier import (
    WalletCohortReplayStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_cohort_audit.v1"


@dataclass(frozen=True, slots=True)
class WalletCohortAuditReceipt:
    cohort_id: str
    ledger_receipt_id: str
    replay_id: str
    store_verification_id: str
    replay_matches: bool
    audit_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "cohort_id",
            "ledger_receipt_id",
            "replay_id",
            "store_verification_id",
            "audit_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.replay_matches, bool):
            raise TypeError("replay_matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet cohort audit schema_version")
        if self.audit_id != deterministic_id("wallet_cohort_audit", self.identity_payload()):
            raise ValueError("audit_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "cohort_id": self.cohort_id,
            "ledger_receipt_id": self.ledger_receipt_id,
            "replay_id": self.replay_id,
            "replay_matches": self.replay_matches,
            "schema_version": self.schema_version,
            "store_verification_id": self.store_verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"audit_id": self.audit_id, **self.identity_payload()}


def build_wallet_cohort_audit_receipt(
    *,
    cohort_id: str,
    ledger_receipt: WalletCohortLedgerReceipt,
    replay_receipt: WalletCohortReplayReceipt,
    store_verification: WalletCohortReplayStoreVerificationReceipt,
) -> WalletCohortAuditReceipt:
    if not isinstance(cohort_id, str) or not cohort_id.strip():
        raise ValueError("cohort_id must be non-empty")
    if not isinstance(ledger_receipt, WalletCohortLedgerReceipt):
        raise TypeError("ledger_receipt must be WalletCohortLedgerReceipt")
    if not isinstance(replay_receipt, WalletCohortReplayReceipt):
        raise TypeError("replay_receipt must be WalletCohortReplayReceipt")
    if not isinstance(store_verification, WalletCohortReplayStoreVerificationReceipt):
        raise TypeError(
            "store_verification must be WalletCohortReplayStoreVerificationReceipt"
        )
    if ledger_receipt.cohort_id != cohort_id.strip():
        raise ValueError("ledger receipt cohort_id mismatch")
    if replay_receipt.cohort_id != cohort_id.strip():
        raise ValueError("replay receipt cohort_id mismatch")
    if store_verification.replay_id != replay_receipt.replay_id:
        raise ValueError("store verification replay_id mismatch")
    identity = {
        "cohort_id": cohort_id.strip(),
        "ledger_receipt_id": ledger_receipt.receipt_id,
        "replay_id": replay_receipt.replay_id,
        "replay_matches": replay_receipt.matches and store_verification.matches,
        "schema_version": _SCHEMA_VERSION,
        "store_verification_id": store_verification.verification_id,
    }
    return WalletCohortAuditReceipt(
        **identity,
        audit_id=deterministic_id("wallet_cohort_audit", identity),
    )


__all__ = ["WalletCohortAuditReceipt", "build_wallet_cohort_audit_receipt"]
