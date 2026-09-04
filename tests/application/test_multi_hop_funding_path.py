from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.funding_graph_evidence import FundingGraphEvidence, ingest_funding_graph_evidence
from smart_money.application.funding_graph_read_model import build_funding_graph_read_model
from smart_money.application.multi_hop_funding_path import detect_multi_hop_funding_paths
from smart_money.core.ids import deterministic_id


def _edge(source: str, target: str, amount: int, slot: int) -> FundingGraphEvidence:
    identity = {
        "chain": "solana:mainnet-beta", "native_amount": amount, "observed_slot": slot,
        "provenance": {"source": "rpc", "signature": f"sig-{slot}"},
        "schema_version": "funding_graph_evidence.v1", "source_wallet": source,
        "target_wallet": target, "transaction_signature": f"sig-{slot}",
    }
    return FundingGraphEvidence(**identity, evidence_id=deterministic_id("funding_graph_evidence", identity))


def test_multi_hop_path_detection_is_deterministic_and_cycle_free() -> None:
    ledger = EvidenceGroundingLedger()
    for edge in (_edge("A", "B", 100, 1), _edge("B", "C", 50, 2), _edge("C", "A", 20, 3)):
        ingest_funding_graph_evidence(edge, ledger)
    model = build_funding_graph_read_model(ledger)
    paths = detect_multi_hop_funding_paths(model, source_wallet="A", target_wallet="C", max_hops=3)
    assert len(paths) == 1
    assert paths[0].wallets == ("A", "B", "C")
    assert paths[0].total_native_amount == 150
    assert paths == detect_multi_hop_funding_paths(model, source_wallet="A", target_wallet="C", max_hops=3)
