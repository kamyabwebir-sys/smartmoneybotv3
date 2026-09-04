from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "funding_graph_evidence.v1"


@dataclass(frozen=True, slots=True)
class FundingGraphEvidence:
    source_wallet: str
    target_wallet: str
    chain: str
    observed_slot: int
    native_amount: int
    transaction_signature: str
    provenance: Mapping[str, str]
    evidence_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("source_wallet", "target_wallet", "chain", "transaction_signature", "evidence_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.source_wallet.strip() == self.target_wallet.strip():
            raise ValueError("source_wallet and target_wallet must differ")
        if isinstance(self.observed_slot, bool) or not isinstance(self.observed_slot, int) or self.observed_slot < 0:
            raise ValueError("observed_slot must be non-negative integer")
        if isinstance(self.native_amount, bool) or not isinstance(self.native_amount, int) or self.native_amount < 0:
            raise ValueError("native_amount must be non-negative integer")
        if not isinstance(self.provenance, Mapping) or not self.provenance or not all(
            isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip()
            for k, v in self.provenance.items()
        ):
            raise ValueError("provenance must contain non-empty text")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding graph evidence schema_version")
        if self.evidence_id != deterministic_id("funding_graph_evidence", self.identity_payload()):
            raise ValueError("evidence_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "chain": self.chain.strip(),
            "native_amount": self.native_amount,
            "observed_slot": self.observed_slot,
            "provenance": dict(sorted(self.provenance.items())),
            "schema_version": self.schema_version,
            "source_wallet": self.source_wallet.strip(),
            "target_wallet": self.target_wallet.strip(),
            "transaction_signature": self.transaction_signature.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"evidence_id": self.evidence_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class FundingGraphLedgerReceipt:
    evidence_id: str
    ledger_entry_count: int
    already_present: bool
    receipt_id: str
    schema_version: str = "funding_graph_ledger.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or not self.evidence_id.strip():
            raise ValueError("evidence_id must be non-empty")
        if isinstance(self.ledger_entry_count, bool) or not isinstance(self.ledger_entry_count, int) or self.ledger_entry_count < 0:
            raise ValueError("ledger_entry_count must be non-negative integer")
        if not isinstance(self.already_present, bool):
            raise TypeError("already_present must be boolean")
        if self.receipt_id != deterministic_id("funding_graph_ledger", self.identity_payload()):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "already_present": self.already_present,
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def ingest_funding_graph_evidence(
    evidence: FundingGraphEvidence, ledger: EvidenceLedger
) -> FundingGraphLedgerReceipt:
    if not isinstance(evidence, FundingGraphEvidence):
        raise TypeError("evidence must be FundingGraphEvidence")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="funding_graph",
        evidence_type="funding_graph_evidence",
        timestamp=evidence.observed_slot,
        data={"funding_graph": evidence.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
            "provenance": dict(evidence.provenance),
        },
    )
    evidence_id = payload.get_canonical_id()
    already_present = ledger.contains(evidence_id)
    before_count = ledger.entry_count
    if evidence_id != payload.get_canonical_id() or ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained funding graph payload mismatch")
    expected_count = before_count if already_present else before_count + 1
    if ledger.entry_count != expected_count:
        raise ValueError("Ledger entry count violates idempotent append contract")
    identity = {"already_present": already_present, "evidence_id": evidence_id, "ledger_entry_count": ledger.entry_count, "schema_version": "funding_graph_ledger.v1"}
    return FundingGraphLedgerReceipt(
        evidence_id=evidence_id,
        ledger_entry_count=ledger.entry_count,
        already_present=already_present,
        receipt_id=deterministic_id("funding_graph_ledger", identity),
    )


__all__ = ["FundingGraphEvidence", "FundingGraphLedgerReceipt", "ingest_funding_graph_evidence"]
