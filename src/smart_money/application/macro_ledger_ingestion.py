from __future__ import annotations

from dataclasses import dataclass

from smart_money.application.macro_evidence_projection import (
    ExternalMacroEvidenceProjection,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.domain.macro_context import MacroEvidenceObservation

_SCHEMA_VERSION = "macro_ledger_ingestion.v1"


@dataclass(frozen=True, slots=True)
class MacroLedgerIngestionReceipt:
    """Deterministic receipt for one idempotent macro Evidence append."""

    receipt_id: str
    observation_id: str
    evidence_id: str
    source_id: str
    ledger_entry_count: int
    already_present: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "receipt_id",
            "observation_id",
            "evidence_id",
            "source_id",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if isinstance(self.ledger_entry_count, bool) or not isinstance(
            self.ledger_entry_count,
            int,
        ):
            raise TypeError("ledger_entry_count must be an integer")
        if self.ledger_entry_count < 0:
            raise ValueError("ledger_entry_count must be non-negative")
        if not isinstance(self.already_present, bool):
            raise TypeError("already_present must be a boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported macro ledger ingestion schema_version")
        if self.receipt_id != deterministic_id(
            "macro_ledger_ingestion",
            self.identity_payload(),
        ):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, str | int | bool]:
        return {
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "observation_id": self.observation_id,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
        }

    def canonical_dict(self) -> dict[str, str | int | bool]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def ingest_macro_evidence(
    observation: MacroEvidenceObservation,
    ledger: EvidenceLedger,
) -> MacroLedgerIngestionReceipt:
    """Project and append one macro observation with fail-closed identity checks."""
    if not isinstance(observation, MacroEvidenceObservation):
        raise TypeError("observation must be a MacroEvidenceObservation")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")

    projection = ExternalMacroEvidenceProjection.from_observation(observation)
    payload = projection.payload
    evidence_id = payload.get_canonical_id()
    if evidence_id != projection.payload.get_canonical_id():
        raise ValueError("projection evidence identity is unstable")

    already_present = ledger.contains(evidence_id)
    before_count = ledger.entry_count
    returned_id = ledger.append(payload)
    if returned_id != evidence_id:
        raise ValueError("Ledger returned a mismatched evidence identity")
    retained = ledger.get(evidence_id)
    if retained != payload:
        raise ValueError("Ledger retained payload does not match projection")
    after_count = ledger.entry_count
    expected_count = before_count if already_present else before_count + 1
    if after_count != expected_count:
        raise ValueError("Ledger entry count violates idempotent append contract")

    identity = {
        "evidence_id": evidence_id,
        "ledger_entry_count": after_count,
        "observation_id": observation.canonical_id,
        "schema_version": _SCHEMA_VERSION,
        "source_id": observation.source_id,
    }
    return MacroLedgerIngestionReceipt(
        receipt_id=deterministic_id("macro_ledger_ingestion", identity),
        observation_id=observation.canonical_id,
        evidence_id=evidence_id,
        source_id=observation.source_id,
        ledger_entry_count=after_count,
        already_present=already_present,
    )


__all__ = ["MacroLedgerIngestionReceipt", "ingest_macro_evidence"]
