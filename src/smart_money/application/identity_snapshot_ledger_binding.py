from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.identity_audit_snapshot_store import (
    IdentityAuditSnapshot,
)
from smart_money.application.identity_evidence_projection import (
    IdentityEvidenceProjection,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.domain.identity_evidence import IdentityEvidence

_SCHEMA_VERSION = "identity_snapshot_ledger_binding.v1"


@dataclass(frozen=True, slots=True)
class IdentitySnapshotLedgerBindingReceipt:
    """Deterministic linkage between an audit snapshot and a Ledger payload."""

    receipt_id: str
    snapshot_evidence_id: str
    identity_evidence_id: str
    ledger_evidence_id: str
    source_id: str
    timestamp: int
    ledger_entry_count: int
    already_present: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "snapshot_evidence_id",
            "identity_evidence_id",
            "ledger_evidence_id",
            "source_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        for name in ("timestamp", "ledger_entry_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
        if self.ledger_entry_count < 1:
            raise ValueError("ledger_entry_count must be positive")
        if not isinstance(self.already_present, bool):
            raise TypeError("already_present must be a boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported identity snapshot binding schema_version")
        if self.receipt_id != deterministic_id(
            "identity_snapshot_ledger_binding", self.identity_payload()
        ):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "already_present": self.already_present,
            "identity_evidence_id": self.identity_evidence_id,
            "ledger_evidence_id": self.ledger_evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "schema_version": self.schema_version,
            "snapshot_evidence_id": self.snapshot_evidence_id,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def bind_identity_snapshot_to_ledger(
    snapshot: IdentityAuditSnapshot,
    evidence: IdentityEvidence,
    ledger: EvidenceLedger,
    *,
    timestamp: int,
) -> IdentitySnapshotLedgerBindingReceipt:
    """Append the snapshot's source evidence and verify the linkage fail-closed."""
    if not isinstance(snapshot, IdentityAuditSnapshot):
        raise TypeError("snapshot must be an IdentityAuditSnapshot")
    if not isinstance(evidence, IdentityEvidence):
        raise TypeError("evidence must be an IdentityEvidence")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if isinstance(timestamp, bool) or not isinstance(timestamp, int):
        raise TypeError("timestamp must be an integer")
    if snapshot.evidence_id != evidence.evidence_id:
        raise ValueError("snapshot does not match identity evidence")
    expected_snapshot = IdentityAuditSnapshot.from_evidence(evidence)
    if expected_snapshot != snapshot:
        raise ValueError("snapshot content does not match identity evidence")

    projection = IdentityEvidenceProjection.from_evidence(
        evidence,
        timestamp=timestamp,
    )
    ledger_evidence_id = projection.payload.get_canonical_id()
    already_present = ledger.contains(ledger_evidence_id)
    before_count = ledger.entry_count
    returned_id = ledger.append(projection.payload)
    if returned_id != ledger_evidence_id:
        raise ValueError("Ledger returned a mismatched evidence identity")
    retained = ledger.get(ledger_evidence_id)
    if retained != projection.payload:
        raise ValueError("Ledger retained payload does not match projection")
    expected_count = before_count if already_present else before_count + 1
    if ledger.entry_count != expected_count:
        raise ValueError("Ledger entry count violates idempotent append contract")
    identity = {
        "already_present": already_present,
        "identity_evidence_id": evidence.evidence_id,
        "ledger_evidence_id": ledger_evidence_id,
        "ledger_entry_count": ledger.entry_count,
        "schema_version": _SCHEMA_VERSION,
        "snapshot_evidence_id": snapshot.evidence_id,
        "source_id": evidence.source_id,
        "timestamp": timestamp,
    }
    return IdentitySnapshotLedgerBindingReceipt(
        receipt_id=deterministic_id("identity_snapshot_ledger_binding", identity),
        snapshot_evidence_id=snapshot.evidence_id,
        identity_evidence_id=evidence.evidence_id,
        ledger_evidence_id=ledger_evidence_id,
        source_id=evidence.source_id,
        timestamp=timestamp,
        ledger_entry_count=ledger.entry_count,
        already_present=already_present,
    )


__all__ = [
    "IdentitySnapshotLedgerBindingReceipt",
    "bind_identity_snapshot_to_ledger",
]
