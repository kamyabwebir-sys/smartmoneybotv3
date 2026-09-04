from __future__ import annotations

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.wallet_relationship_intelligence import (
    WalletRelationshipIntelligence,
)
from smart_money.ingestion.contracts import EvidencePayload


def ingest_wallet_relationship_intelligence(
    intelligence: WalletRelationshipIntelligence,
    ledger: EvidenceLedger,
) -> str:
    if not isinstance(intelligence, WalletRelationshipIntelligence):
        raise TypeError("intelligence must be WalletRelationshipIntelligence")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="wallet_relationship_intelligence",
        evidence_type="wallet_relationship_intelligence",
        timestamp=0,
        data={"wallet_relationship_intelligence": intelligence.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
        },
    )
    evidence_id = payload.get_canonical_id()
    if ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained wallet relationship intelligence payload mismatch")
    return evidence_id


__all__ = ["ingest_wallet_relationship_intelligence"]
