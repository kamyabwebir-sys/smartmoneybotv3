from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.token_safety_candidate_binding import (
    TokenSafetyCandidateBinding,
)
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "token_safety_candidate_binding_ledger.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateBindingLedgerReceipt:
    receipt_id: str
    binding_id: str
    evidence_id: str
    ledger_entry_count: int
    already_present: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("receipt_id", "binding_id", "evidence_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if (
            isinstance(self.ledger_entry_count, bool)
            or not isinstance(self.ledger_entry_count, int)
            or self.ledger_entry_count < 0
        ):
            raise ValueError("ledger_entry_count must be non-negative integer")
        if not isinstance(self.already_present, bool):
            raise TypeError("already_present must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported binding ledger schema_version")
        if self.receipt_id != deterministic_id(
            "token_safety_candidate_binding_ledger", self.identity_payload()
        ):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "already_present": self.already_present,
            "binding_id": self.binding_id,
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def ingest_token_safety_candidate_binding(
    binding: TokenSafetyCandidateBinding, ledger: EvidenceLedger
) -> TokenSafetyCandidateBindingLedgerReceipt:
    if not isinstance(binding, TokenSafetyCandidateBinding):
        raise TypeError("binding must be TokenSafetyCandidateBinding")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="token_safety",
        evidence_type="token_safety_candidate_binding",
        timestamp=0,
        data={"binding": binding.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
            "provenance": {
                "binding_id": binding.binding_id,
                "candidate_id": binding.candidate_id,
                "token_observation_id": binding.token_observation_id,
                "source_id": "token_safety",
                "source_schema_version": binding.schema_version,
            },
        },
    )
    evidence_id = payload.get_canonical_id()
    already_present = ledger.contains(evidence_id)
    before_count = ledger.entry_count
    if ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained binding payload mismatch")
    expected_count = before_count if already_present else before_count + 1
    if ledger.entry_count != expected_count:
        raise ValueError("Ledger entry count violates idempotent append contract")
    identity = {
        "already_present": already_present,
        "binding_id": binding.binding_id,
        "evidence_id": evidence_id,
        "ledger_entry_count": ledger.entry_count,
        "schema_version": _SCHEMA_VERSION,
    }
    return TokenSafetyCandidateBindingLedgerReceipt(
        receipt_id=deterministic_id(
            "token_safety_candidate_binding_ledger", identity
        ),
        binding_id=binding.binding_id,
        evidence_id=evidence_id,
        ledger_entry_count=ledger.entry_count,
        already_present=already_present,
    )


__all__ = [
    "TokenSafetyCandidateBindingLedgerReceipt",
    "ingest_token_safety_candidate_binding",
]
