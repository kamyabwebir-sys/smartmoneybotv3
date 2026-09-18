from __future__ import annotations

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.wallet_ranking import WalletRanking
from smart_money.ingestion.contracts import EvidencePayload


def ingest_wallet_ranking(
    ranking: WalletRanking,
    ledger: EvidenceLedger,
) -> str:
    if not isinstance(ranking, WalletRanking):
        raise TypeError("ranking must be WalletRanking")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="wallet_ranking",
        evidence_type="wallet_ranking",
        timestamp=0,
        data={"wallet_ranking": ranking.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
        },
    )
    evidence_id = payload.get_canonical_id()
    if ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained wallet ranking payload mismatch")
    return evidence_id


__all__ = ["ingest_wallet_ranking"]
