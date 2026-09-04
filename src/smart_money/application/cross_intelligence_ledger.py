from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.cross_intelligence import WalletTokenCrossSubjectContract, CrossIntelligenceEvidenceProjection

@dataclass(frozen=True, slots=True)
class CrossIntelligenceLedgerReceipt:
    cross_id: str
    evidence_id: str
    already_present: bool

def ingest_cross_intelligence(contract: WalletTokenCrossSubjectContract, ledger: EvidenceLedger) -> CrossIntelligenceLedgerReceipt:
    if not isinstance(contract, WalletTokenCrossSubjectContract) or not isinstance(ledger, EvidenceLedger):
        raise TypeError("invalid contract or ledger")
    payload = CrossIntelligenceEvidenceProjection.from_contract(contract).payload
    evidence_id = payload.get_canonical_id()
    present = ledger.contains(evidence_id)
    if ledger.append(payload) != evidence_id:
        raise ValueError("ledger identity mismatch")
    return CrossIntelligenceLedgerReceipt(contract.cross_id, evidence_id, present)

__all__ = ["CrossIntelligenceLedgerReceipt", "ingest_cross_intelligence"]
