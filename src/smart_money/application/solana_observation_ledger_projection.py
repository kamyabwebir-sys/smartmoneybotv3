from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_observation_parser import (
    SolanaObservationParser,
)
from smart_money.core.ids import deterministic_id
from smart_money.core.serialization import canonicalize
from smart_money.domain.solana_observation import SolanaChainObservation

_SCHEMA_VERSION = "solana_observation_ledger_projection.v1"


@dataclass(frozen=True, slots=True)
class SolanaObservationLedgerReceipt:
    """Deterministic receipt for one idempotent Solana observation append."""

    receipt_id: str
    observation_id: str
    evidence_id: str
    source_id: str
    ledger_entry_count: int
    already_present: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "observation_id",
            "evidence_id",
            "source_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if isinstance(self.ledger_entry_count, bool) or not isinstance(
            self.ledger_entry_count, int
        ):
            raise TypeError("ledger_entry_count must be an integer")
        if self.ledger_entry_count < 0:
            raise ValueError("ledger_entry_count must be non-negative")
        if not isinstance(self.already_present, bool):
            raise TypeError("already_present must be a boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported Solana ledger projection schema_version")
        if self.receipt_id != deterministic_id(
            "solana_observation_ledger", self.identity_payload()
        ):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "already_present": self.already_present,
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "observation_id": self.observation_id,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def ingest_solana_observation(
    observation: SolanaChainObservation,
    ledger: EvidenceLedger,
) -> SolanaObservationLedgerReceipt:
    """Project and append one Solana observation with fail-closed checks."""
    if not isinstance(observation, SolanaChainObservation):
        raise TypeError("observation must be a SolanaChainObservation")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")

    projection = SolanaObservationParser.from_observation(observation)
    payload = projection.payload
    evidence_id = payload.get_canonical_id()
    if evidence_id != payload.get_canonical_id():
        raise ValueError("projection evidence identity is unstable")
    already_present = ledger.contains(evidence_id)
    before_count = ledger.entry_count
    returned_id = ledger.append(payload)
    if returned_id != evidence_id:
        raise ValueError("Ledger returned a mismatched evidence identity")
    retained = ledger.get(evidence_id)
    if retained != payload:
        raise ValueError("Ledger retained payload does not match projection")
    expected_count = before_count if already_present else before_count + 1
    if ledger.entry_count != expected_count:
        raise ValueError("Ledger entry count violates idempotent append contract")
    identity = {
        "already_present": already_present,
        "evidence_id": evidence_id,
        "ledger_entry_count": ledger.entry_count,
        "observation_id": observation.observation_id,
        "schema_version": _SCHEMA_VERSION,
        "source_id": payload.source_id,
    }
    return SolanaObservationLedgerReceipt(
        receipt_id=deterministic_id("solana_observation_ledger", identity),
        observation_id=observation.observation_id,
        evidence_id=evidence_id,
        source_id=payload.source_id,
        ledger_entry_count=ledger.entry_count,
        already_present=already_present,
    )


@dataclass(frozen=True, slots=True)
class SolanaObservationReplayReceipt:
    """Deterministic proof that persisted Solana evidence replays identically."""

    receipt_id: str
    observation_id: str
    evidence_id: str
    source_id: str
    ledger_entry_count: int
    schema_version: str = "solana_observation_replay.v1"

    def __post_init__(self) -> None:
        for name in ("receipt_id", "observation_id", "evidence_id", "source_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if isinstance(self.ledger_entry_count, bool) or not isinstance(
            self.ledger_entry_count, int
        ):
            raise TypeError("ledger_entry_count must be an integer")
        if self.ledger_entry_count < 1:
            raise ValueError("ledger_entry_count must be positive")
        if self.schema_version != "solana_observation_replay.v1":
            raise ValueError("unsupported Solana replay schema_version")
        if self.receipt_id != deterministic_id(
            "solana_observation_replay", self.identity_payload()
        ):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "observation_id": self.observation_id,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def verify_solana_observation_replay(
    observation: SolanaChainObservation,
    ledger: EvidenceLedger,
) -> SolanaObservationReplayReceipt:
    """Fail closed unless persisted Solana evidence matches its observation."""
    if not isinstance(observation, SolanaChainObservation):
        raise TypeError("observation must be a SolanaChainObservation")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    expected = SolanaObservationParser.from_observation(observation)
    evidence_id = expected.payload.get_canonical_id()
    retained = ledger.get(evidence_id)
    if retained is None:
        raise ValueError("persisted Solana observation is missing from Ledger")
    if canonicalize(retained.canonical_dict()) != canonicalize(
        expected.payload.canonical_dict()
    ):
        raise ValueError("persisted Solana observation does not match source")
    parsed = SolanaObservationParser.from_payload(retained)
    if parsed.observation_id != observation.observation_id:
        raise ValueError("persisted Solana observation identity mismatch")
    identity = {
        "evidence_id": evidence_id,
        "ledger_entry_count": ledger.entry_count,
        "observation_id": observation.observation_id,
        "schema_version": "solana_observation_replay.v1",
        "source_id": retained.source_id,
    }
    return SolanaObservationReplayReceipt(
        receipt_id=deterministic_id("solana_observation_replay", identity),
        observation_id=observation.observation_id,
        evidence_id=evidence_id,
        source_id=retained.source_id,
        ledger_entry_count=ledger.entry_count,
    )


__all__ = [
    "SolanaObservationLedgerReceipt",
    "SolanaObservationReplayReceipt",
    "ingest_solana_observation",
    "verify_solana_observation_replay",
]
