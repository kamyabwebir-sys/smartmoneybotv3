from __future__ import annotations

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.wallet_candidate_evidence import WalletCandidateEvidence
from smart_money.ingestion.contracts import EvidencePayload


def ingest_wallet_candidate_evidence(
    evidence: WalletCandidateEvidence,
    ledger: EvidenceLedger,
) -> str:
    if not isinstance(evidence, WalletCandidateEvidence):
        raise TypeError("evidence must be WalletCandidateEvidence")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="wallet_candidate",
        evidence_type="wallet_candidate_evidence",
        timestamp=0,
        data={"wallet_candidate": evidence.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": evidence.status.value,
            "provenance": dict(evidence.provenance),
        },
    )
    evidence_id = payload.get_canonical_id()
    if ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained wallet candidate evidence mismatch")
    return evidence_id


__all__ = ["ingest_wallet_candidate_evidence"]
