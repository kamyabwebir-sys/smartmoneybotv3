from __future__ import annotations

from dataclasses import dataclass

from smart_money.application.macro_evidence_projection import (
    ExternalMacroEvidenceProjection,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.core.serialization import canonicalize
from smart_money.domain.macro_context import MacroEvidenceObservation

_SCHEMA_VERSION = "macro_evidence_replay.v1"


@dataclass(frozen=True, slots=True)
class MacroEvidenceReplayReceipt:
    """Deterministic proof that persisted macro Evidence replayed identically."""

    receipt_id: str
    observation_id: str
    evidence_id: str
    source_id: str
    ledger_entry_count: int
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
        if self.ledger_entry_count < 1:
            raise ValueError("ledger_entry_count must be positive")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported macro replay schema_version")
        expected_id = deterministic_id(
            "macro_evidence_replay",
            self.identity_payload(),
        )
        if self.receipt_id != expected_id:
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, str | int]:
        return {
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "observation_id": self.observation_id,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
        }

    def canonical_dict(self) -> dict[str, str | int]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def verify_macro_evidence_replay(
    observation: MacroEvidenceObservation,
    ledger: EvidenceLedger,
) -> MacroEvidenceReplayReceipt:
    """Fail closed unless persisted macro Evidence matches its source observation."""
    if not isinstance(observation, MacroEvidenceObservation):
        raise TypeError("observation must be a MacroEvidenceObservation")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")

    expected = ExternalMacroEvidenceProjection.from_observation(observation)
    evidence_id = expected.payload.get_canonical_id()
    retained = ledger.get(evidence_id)
    if retained is None:
        raise ValueError("persisted macro Evidence is missing from Ledger")
    if canonicalize(retained.canonical_dict()) != canonicalize(
        expected.payload.canonical_dict()
    ):
        raise ValueError("persisted macro Evidence does not match source observation")
    parsed = ExternalMacroEvidenceProjection(
        payload=retained,
        observation_id=observation.canonical_id,
    )
    if parsed.observation_id != observation.canonical_id:
        raise ValueError("persisted macro observation identity mismatch")

    identity = {
        "evidence_id": evidence_id,
        "ledger_entry_count": ledger.entry_count,
        "observation_id": observation.canonical_id,
        "schema_version": _SCHEMA_VERSION,
        "source_id": observation.source_id,
    }
    return MacroEvidenceReplayReceipt(
        receipt_id=deterministic_id("macro_evidence_replay", identity),
        observation_id=observation.canonical_id,
        evidence_id=evidence_id,
        source_id=observation.source_id,
        ledger_entry_count=ledger.entry_count,
    )


__all__ = ["MacroEvidenceReplayReceipt", "verify_macro_evidence_replay"]
