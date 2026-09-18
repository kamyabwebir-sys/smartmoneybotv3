from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.multi_hop_funding_path import MultiHopFundingPath
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "wallet_relationship_evidence.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipEvidence:
    source_wallet: str
    target_wallet: str
    relationship_type: str
    path_id: str
    edge_evidence_ids: tuple[str, ...]
    provenance: Mapping[str, str]
    relationship_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("source_wallet", "target_wallet", "relationship_type", "path_id", "relationship_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.source_wallet.strip() == self.target_wallet.strip():
            raise ValueError("source_wallet and target_wallet must differ")
        if self.relationship_type not in {"DIRECT_FUNDING", "MULTI_HOP_FUNDING"}:
            raise ValueError("unsupported relationship_type")
        if not isinstance(self.edge_evidence_ids, tuple) or len(self.edge_evidence_ids) < 1:
            raise ValueError("edge_evidence_ids must be non-empty")
        if not all(isinstance(item, str) and item.strip() for item in self.edge_evidence_ids):
            raise ValueError("edge_evidence_ids must contain non-empty strings")
        if not isinstance(self.provenance, Mapping) or not self.provenance:
            raise ValueError("provenance must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet relationship schema_version")
        if self.relationship_id != deterministic_id("wallet_relationship_evidence", self.identity_payload()):
            raise ValueError("relationship_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "edge_evidence_ids": self.edge_evidence_ids,
            "path_id": self.path_id.strip(),
            "provenance": dict(sorted(self.provenance.items())),
            "relationship_type": self.relationship_type,
            "schema_version": self.schema_version,
            "source_wallet": self.source_wallet.strip(),
            "target_wallet": self.target_wallet.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"relationship_id": self.relationship_id, **self.identity_payload()}


def project_funding_path_relationship(
    path: MultiHopFundingPath,
    *,
    provenance: Mapping[str, str],
) -> WalletRelationshipEvidence:
    if not isinstance(path, MultiHopFundingPath):
        raise TypeError("path must be MultiHopFundingPath")
    if not isinstance(provenance, Mapping) or not provenance:
        raise ValueError("provenance must be non-empty")
    identity = {
        "edge_evidence_ids": path.edge_evidence_ids,
        "path_id": path.path_id,
        "provenance": dict(sorted(provenance.items())),
        "relationship_type": "DIRECT_FUNDING" if len(path.wallets) == 2 else "MULTI_HOP_FUNDING",
        "schema_version": _SCHEMA_VERSION,
        "source_wallet": path.wallets[0],
        "target_wallet": path.wallets[-1],
    }
    return WalletRelationshipEvidence(
        **identity,
        relationship_id=deterministic_id("wallet_relationship_evidence", identity),
    )


def ingest_wallet_relationship_evidence(
    relationship: WalletRelationshipEvidence, ledger: EvidenceLedger
) -> str:
    if not isinstance(relationship, WalletRelationshipEvidence):
        raise TypeError("relationship must be WalletRelationshipEvidence")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="wallet_intelligence",
        evidence_type="wallet_relationship_evidence",
        timestamp=0,
        data={"wallet_relationship": relationship.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
            "provenance": dict(relationship.provenance),
        },
    )
    evidence_id = payload.get_canonical_id()
    if ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained wallet relationship payload mismatch")
    return evidence_id


__all__ = [
    "WalletRelationshipEvidence",
    "project_funding_path_relationship",
    "ingest_wallet_relationship_evidence",
]
