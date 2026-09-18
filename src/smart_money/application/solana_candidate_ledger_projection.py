from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "solana_candidate_ledger_projection.v1"


@dataclass(frozen=True, slots=True)
class SolanaCandidateLedgerReceipt:
    receipt_id: str
    candidate_id: str
    evidence_id: str
    ledger_entry_count: int
    already_present: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("receipt_id", "candidate_id", "evidence_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if isinstance(self.ledger_entry_count, bool) or not isinstance(self.ledger_entry_count, int):
            raise TypeError("ledger_entry_count must be an integer")
        if self.ledger_entry_count < 0 or not isinstance(self.already_present, bool):
            raise ValueError("invalid ledger receipt fields")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported candidate ledger schema_version")
        if self.receipt_id != deterministic_id(
            "solana_candidate_ledger", self.identity_payload()
        ):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "already_present": self.already_present,
            "candidate_id": self.candidate_id,
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def ingest_solana_candidate(
    candidate: SolanaWalletTokenCandidate, ledger: EvidenceLedger
) -> SolanaCandidateLedgerReceipt:
    if not isinstance(candidate, SolanaWalletTokenCandidate):
        raise TypeError("candidate must be SolanaWalletTokenCandidate")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="solana",
        evidence_type="solana_wallet_token_candidate",
        timestamp=candidate.first_slot,
        data={"candidate": candidate.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
            "provenance": {
                "candidate_id": candidate.candidate_id,
                "source_id": "solana",
                "source_schema_version": candidate.schema_version,
            },
        },
    )
    evidence_id = payload.get_canonical_id()
    already_present = ledger.contains(evidence_id)
    before = ledger.entry_count
    if ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained candidate payload mismatch")
    if ledger.entry_count != (before if already_present else before + 1):
        raise ValueError("Ledger entry count violates idempotent append contract")
    identity = {
        "already_present": already_present,
        "candidate_id": candidate.candidate_id,
        "evidence_id": evidence_id,
        "ledger_entry_count": ledger.entry_count,
        "schema_version": _SCHEMA_VERSION,
    }
    return SolanaCandidateLedgerReceipt(
        receipt_id=deterministic_id("solana_candidate_ledger", identity),
        candidate_id=candidate.candidate_id,
        evidence_id=evidence_id,
        ledger_entry_count=ledger.entry_count,
        already_present=already_present,
    )


__all__ = ["SolanaCandidateLedgerReceipt", "ingest_solana_candidate"]
