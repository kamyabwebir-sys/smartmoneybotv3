from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_cluster_detection import FundingCluster
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "funding_cluster_ledger.v1"


@dataclass(frozen=True, slots=True)
class FundingClusterLedgerReceipt:
    receipt_id: str
    cluster_id: str
    evidence_id: str
    ledger_entry_count: int
    already_present: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("receipt_id", "cluster_id", "evidence_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if isinstance(self.ledger_entry_count, bool) or not isinstance(self.ledger_entry_count, int) or self.ledger_entry_count < 0:
            raise ValueError("ledger_entry_count must be non-negative integer")
        if not isinstance(self.already_present, bool):
            raise TypeError("already_present must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster ledger schema_version")
        if self.receipt_id != deterministic_id("funding_cluster_ledger", self.identity_payload()):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "already_present": self.already_present,
            "cluster_id": self.cluster_id,
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def ingest_funding_cluster(
    cluster: FundingCluster, ledger: EvidenceLedger
) -> FundingClusterLedgerReceipt:
    if not isinstance(cluster, FundingCluster):
        raise TypeError("cluster must be FundingCluster")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="funding_graph",
        evidence_type="funding_cluster",
        timestamp=0,
        data={"funding_cluster": cluster.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
            "provenance": {
                "cluster_id": cluster.cluster_id,
                "relationship_ids": ",".join(cluster.relationship_ids),
                "source_id": "funding_graph",
                "source_schema_version": cluster.schema_version,
            },
        },
    )
    evidence_id = payload.get_canonical_id()
    already_present = ledger.contains(evidence_id)
    before_count = ledger.entry_count
    if ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained funding cluster payload mismatch")
    expected_count = before_count if already_present else before_count + 1
    if ledger.entry_count != expected_count:
        raise ValueError("Ledger entry count violates idempotent append contract")
    identity = {
        "already_present": already_present,
        "cluster_id": cluster.cluster_id,
        "evidence_id": evidence_id,
        "ledger_entry_count": ledger.entry_count,
        "schema_version": _SCHEMA_VERSION,
    }
    return FundingClusterLedgerReceipt(
        receipt_id=deterministic_id("funding_cluster_ledger", identity),
        cluster_id=cluster.cluster_id,
        evidence_id=evidence_id,
        ledger_entry_count=ledger.entry_count,
        already_present=already_present,
    )


__all__ = ["FundingClusterLedgerReceipt", "ingest_funding_cluster"]
