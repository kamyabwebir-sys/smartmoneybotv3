from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.wallet_cohort_detection import WalletCohort
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "wallet_cohort_ledger.v1"


@dataclass(frozen=True, slots=True)
class WalletCohortLedgerReceipt:
    receipt_id: str
    cohort_id: str
    evidence_id: str
    ledger_entry_count: int
    already_present: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("receipt_id", "cohort_id", "evidence_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if isinstance(self.ledger_entry_count, bool) or not isinstance(self.ledger_entry_count, int) or self.ledger_entry_count < 0:
            raise ValueError("ledger_entry_count must be non-negative integer")
        if not isinstance(self.already_present, bool):
            raise TypeError("already_present must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet cohort ledger schema_version")
        if self.receipt_id != deterministic_id("wallet_cohort_ledger", self.identity_payload()):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "already_present": self.already_present,
            "cohort_id": self.cohort_id,
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def ingest_wallet_cohort(cohort: WalletCohort, ledger: EvidenceLedger) -> WalletCohortLedgerReceipt:
    if not isinstance(cohort, WalletCohort):
        raise TypeError("cohort must be WalletCohort")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="wallet_intelligence",
        evidence_type="wallet_cohort",
        timestamp=0,
        data={"wallet_cohort": cohort.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
            "provenance": {
                "cohort_id": cohort.cohort_id,
                "fingerprint_ids": ",".join(cohort.fingerprint_ids),
                "source_id": "wallet_intelligence",
                "source_schema_version": cohort.schema_version,
            },
        },
    )
    evidence_id = payload.get_canonical_id()
    already_present = ledger.contains(evidence_id)
    before_count = ledger.entry_count
    if ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained wallet cohort payload mismatch")
    expected_count = before_count if already_present else before_count + 1
    if ledger.entry_count != expected_count:
        raise ValueError("Ledger entry count violates idempotent append contract")
    identity = {
        "already_present": already_present,
        "cohort_id": cohort.cohort_id,
        "evidence_id": evidence_id,
        "ledger_entry_count": ledger.entry_count,
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletCohortLedgerReceipt(
        receipt_id=deterministic_id("wallet_cohort_ledger", identity),
        cohort_id=cohort.cohort_id,
        evidence_id=evidence_id,
        ledger_entry_count=ledger.entry_count,
        already_present=already_present,
    )


__all__ = ["WalletCohortLedgerReceipt", "ingest_wallet_cohort"]
