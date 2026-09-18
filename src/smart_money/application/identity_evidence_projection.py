from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.core.serialization import canonicalize
from smart_money.domain.identity_evidence import IdentityEvidence
from smart_money.ingestion.contracts import EvidencePayload

_EVIDENCE_TYPE = "identity_evidence"
_SCHEMA_VERSION = "identity_evidence_projection.v1"


@dataclass(frozen=True, slots=True)
class IdentityEvidenceProjection:
    """Application-bound, non-authoritative projection of identity evidence."""

    EVIDENCE_TYPE: ClassVar[str] = _EVIDENCE_TYPE
    payload: EvidencePayload
    evidence_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        if self.payload.evidence_type != self.EVIDENCE_TYPE:
            raise ValueError("unsupported identity evidence_type")
        if self.evidence_id != self.payload.get_canonical_id():
            raise ValueError("evidence_id does not match payload")
        if set(self.payload.data) != {"identity_evidence"}:
            raise ValueError("identity evidence data keys do not match")
        if set(self.payload.metadata) != {
            "authority",
            "classification",
            "provenance",
            "verification_status",
        }:
            raise ValueError("identity evidence metadata keys do not match")
        if self.payload.metadata["authority"] != "NONE":
            raise ValueError("identity evidence authority mismatch")
        if self.payload.metadata["classification"] != "EVIDENCE":
            raise ValueError("identity evidence classification mismatch")
        identity = self.payload.data["identity_evidence"]
        if not isinstance(identity, Mapping):
            raise ValueError("identity_evidence must be a mapping")
        if not isinstance(identity.get("identity_evidence_id"), str):
            raise ValueError("identity evidence source identity is missing")
        provenance = self.payload.metadata["provenance"]
        if not isinstance(provenance, Mapping):
            raise ValueError("provenance must be a mapping")
        if provenance.get("source_id") != self.payload.source_id:
            raise ValueError("identity evidence provenance source mismatch")

    @classmethod
    def from_evidence(
        cls,
        evidence: IdentityEvidence,
        *,
        timestamp: int,
    ) -> IdentityEvidenceProjection:
        if not isinstance(evidence, IdentityEvidence):
            raise TypeError("evidence must be an IdentityEvidence")
        if isinstance(timestamp, bool) or not isinstance(timestamp, int):
            raise TypeError("timestamp must be an integer")
        payload = EvidencePayload(
            source_id=evidence.source_id,
            evidence_type=cls.EVIDENCE_TYPE,
            timestamp=timestamp,
            data={
                "identity_evidence": {
                    **evidence.canonical_dict(),
                    "identity_evidence_id": evidence.evidence_id,
                }
            },
            metadata={
                "authority": "NONE",
                "classification": "EVIDENCE",
                "verification_status": evidence.status.value,
                "provenance": {
                    **dict(sorted(evidence.provenance.items())),
                    "source_id": evidence.source_id.strip(),
                    "identity_evidence_id": evidence.evidence_id,
                    "source_schema_version": evidence.schema_version,
                },
            },
        )
        return cls(payload=payload, evidence_id=payload.get_canonical_id())

    @classmethod
    def from_identity_evidence(
        cls,
        evidence: IdentityEvidence,
        *,
        timestamp: int,
    ) -> IdentityEvidenceProjection:
        return cls.from_evidence(evidence, timestamp=timestamp)


@dataclass(frozen=True, slots=True)
class IdentityEvidenceLedgerReceipt:
    """Deterministic receipt for one idempotent identity-evidence append."""

    receipt_id: str
    evidence_id: str
    source_id: str
    ledger_entry_count: int
    already_present: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("receipt_id", "evidence_id", "source_id"):
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
            raise ValueError("unsupported identity evidence ledger schema_version")
        if self.receipt_id != deterministic_id(
            "identity_evidence_ledger", self.identity_payload()
        ):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "already_present": self.already_present,
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class IdentityEvidenceReplayReceipt:
    """Deterministic proof that persisted identity evidence replays identically."""

    receipt_id: str
    evidence_id: str
    identity_evidence_id: str
    source_id: str
    ledger_entry_count: int
    schema_version: str = "identity_evidence_replay.v1"

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "evidence_id",
            "identity_evidence_id",
            "source_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if isinstance(self.ledger_entry_count, bool) or not isinstance(
            self.ledger_entry_count, int
        ):
            raise TypeError("ledger_entry_count must be an integer")
        if self.ledger_entry_count < 1:
            raise ValueError("ledger_entry_count must be positive")
        if self.schema_version != "identity_evidence_replay.v1":
            raise ValueError("unsupported identity evidence replay schema_version")
        if self.receipt_id != deterministic_id(
            "identity_evidence_replay", self.identity_payload()
        ):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "identity_evidence_id": self.identity_evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def project_identity_evidence(
    evidence: IdentityEvidence,
    *,
    timestamp: int,
) -> IdentityEvidenceProjection:
    return IdentityEvidenceProjection.from_evidence(evidence, timestamp=timestamp)


def ingest_identity_evidence(
    evidence: IdentityEvidence,
    ledger: EvidenceLedger,
    *,
    timestamp: int,
) -> IdentityEvidenceLedgerReceipt:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    projection = project_identity_evidence(evidence, timestamp=timestamp)
    evidence_id = projection.payload.get_canonical_id()
    if evidence_id != projection.evidence_id:
        raise ValueError("projection evidence identity is unstable")
    already_present = ledger.contains(evidence_id)
    before_count = ledger.entry_count
    returned_id = ledger.append(projection.payload)
    if returned_id != evidence_id:
        raise ValueError("Ledger returned a mismatched evidence identity")
    retained = ledger.get(evidence_id)
    if retained != projection.payload:
        raise ValueError("Ledger retained payload does not match projection")
    expected_count = before_count if already_present else before_count + 1
    if ledger.entry_count != expected_count:
        raise ValueError("Ledger entry count violates idempotent append contract")
    identity = {
        "already_present": already_present,
        "evidence_id": evidence_id,
        "ledger_entry_count": ledger.entry_count,
        "schema_version": _SCHEMA_VERSION,
        "source_id": evidence.source_id,
    }
    return IdentityEvidenceLedgerReceipt(
        receipt_id=deterministic_id("identity_evidence_ledger", identity),
        evidence_id=evidence_id,
        source_id=evidence.source_id,
        ledger_entry_count=ledger.entry_count,
        already_present=already_present,
    )


def verify_identity_evidence_replay(
    evidence: IdentityEvidence,
    ledger: EvidenceLedger,
    *,
    timestamp: int,
) -> IdentityEvidenceReplayReceipt:
    """Fail closed unless persisted identity evidence matches its source."""
    if not isinstance(evidence, IdentityEvidence):
        raise TypeError("evidence must be an IdentityEvidence")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    expected = project_identity_evidence(evidence, timestamp=timestamp)
    evidence_id = expected.payload.get_canonical_id()
    retained = ledger.get(evidence_id)
    if retained is None:
        raise ValueError("persisted identity evidence is missing from Ledger")
    if canonicalize(retained.canonical_dict()) != canonicalize(
        expected.payload.canonical_dict()
    ):
        raise ValueError("persisted identity evidence does not match source evidence")
    parsed = IdentityEvidenceProjection(
        payload=retained,
        evidence_id=evidence_id,
    )
    identity_evidence_id = parsed.payload.data["identity_evidence"][
        "identity_evidence_id"
    ]
    if identity_evidence_id != evidence.evidence_id:
        raise ValueError("persisted identity evidence source identity mismatch")
    return IdentityEvidenceReplayReceipt(
        receipt_id=deterministic_id(
            "identity_evidence_replay",
            {
                "evidence_id": evidence_id,
                "identity_evidence_id": identity_evidence_id,
                "ledger_entry_count": ledger.entry_count,
                "schema_version": "identity_evidence_replay.v1",
                "source_id": evidence.source_id,
            },
        ),
        evidence_id=evidence_id,
        identity_evidence_id=identity_evidence_id,
        source_id=evidence.source_id,
        ledger_entry_count=ledger.entry_count,
    )


__all__ = [
    "IdentityEvidenceLedgerReceipt",
    "IdentityEvidenceReplayReceipt",
    "IdentityEvidenceProjection",
    "ingest_identity_evidence",
    "project_identity_evidence",
    "verify_identity_evidence_replay",
]
