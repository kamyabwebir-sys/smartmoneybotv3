from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_wallet_token_activity import (
    SolanaWalletTokenActivityEvidence,
)
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "solana_wallet_token_activity_ledger.v1"


@dataclass(frozen=True, slots=True)
class SolanaWalletTokenActivityLedgerReceipt:
    receipt_id: str
    activity_id: str
    evidence_id: str
    ledger_entry_count: int
    already_present: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("receipt_id", "activity_id", "evidence_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if isinstance(self.ledger_entry_count, bool) or not isinstance(self.ledger_entry_count, int):
            raise TypeError("ledger_entry_count must be an integer")
        if self.ledger_entry_count < 0 or not isinstance(self.already_present, bool):
            raise ValueError("invalid ledger receipt fields")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported ledger projection schema_version")
        if self.receipt_id != deterministic_id("solana_wallet_token_activity_ledger", self.identity_payload()):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "already_present": self.already_present,
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def ingest_solana_wallet_token_activity(
    activity: SolanaWalletTokenActivityEvidence, ledger: EvidenceLedger
) -> SolanaWalletTokenActivityLedgerReceipt:
    if not isinstance(activity, SolanaWalletTokenActivityEvidence):
        raise TypeError("activity must be SolanaWalletTokenActivityEvidence")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="solana",
        evidence_type="solana_wallet_token_activity",
        timestamp=activity.slot,
        data={"activity": activity.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
            "provenance": {
                "activity_id": activity.activity_id,
                "source_id": "solana",
                "source_schema_version": activity.schema_version,
            },
        },
    )
    evidence_id = payload.get_canonical_id()
    already_present = ledger.contains(evidence_id)
    before = ledger.entry_count
    if ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained activity payload mismatch")
    if ledger.entry_count != (before if already_present else before + 1):
        raise ValueError("Ledger entry count violates idempotent append contract")
    identity = {
        "activity_id": activity.activity_id,
        "already_present": already_present,
        "evidence_id": evidence_id,
        "ledger_entry_count": ledger.entry_count,
        "schema_version": _SCHEMA_VERSION,
    }
    return SolanaWalletTokenActivityLedgerReceipt(
        receipt_id=deterministic_id("solana_wallet_token_activity_ledger", identity),
        activity_id=activity.activity_id,
        evidence_id=evidence_id,
        ledger_entry_count=ledger.entry_count,
        already_present=already_present,
    )


__all__ = ["SolanaWalletTokenActivityLedgerReceipt", "ingest_solana_wallet_token_activity"]
