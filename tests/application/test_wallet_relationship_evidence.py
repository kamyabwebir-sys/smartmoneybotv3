from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.funding_graph_evidence import FundingGraphEvidence, ingest_funding_graph_evidence
from smart_money.application.funding_graph_read_model import build_funding_graph_read_model
from smart_money.application.multi_hop_funding_path import detect_multi_hop_funding_paths
from smart_money.application.wallet_relationship_evidence import (
    ingest_wallet_relationship_evidence,
    project_funding_path_relationship,
)
from smart_money.core.ids import deterministic_id


def _edge(source: str, target: str, slot: int) -> FundingGraphEvidence:
    identity = {
        "chain": "solana:mainnet-beta", "native_amount": 100, "observed_slot": slot,
        "provenance": {"source": "rpc", "signature": f"sig-{slot}"},
        "schema_version": "funding_graph_evidence.v1", "source_wallet": source,
        "target_wallet": target, "transaction_signature": f"sig-{slot}",
    }
    return FundingGraphEvidence(**identity, evidence_id=deterministic_id("funding_graph_evidence", identity))


def test_wallet_relationship_evidence_projects_from_funding_path() -> None:
    ledger = EvidenceGroundingLedger()
    ingest_funding_graph_evidence(_edge("A", "B", 1), ledger)
    ingest_funding_graph_evidence(_edge("B", "C", 2), ledger)
    path = detect_multi_hop_funding_paths(build_funding_graph_read_model(ledger), source_wallet="A", target_wallet="C")[0]
    relationship = project_funding_path_relationship(path, provenance={"source": "funding_graph"})
    evidence_id = ingest_wallet_relationship_evidence(relationship, ledger)
    assert relationship.relationship_type == "MULTI_HOP_FUNDING"
    assert ledger.get(evidence_id).data["wallet_relationship"]["path_id"] == path.path_id
