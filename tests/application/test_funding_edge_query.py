from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.funding_edge_query import query_funding_edges
from smart_money.application.funding_graph_evidence import (
    FundingGraphEvidence,
    ingest_funding_graph_evidence,
)
from smart_money.application.funding_graph_read_model import (
    build_funding_graph_read_model,
)
from smart_money.core.ids import deterministic_id


def _evidence(source: str, target: str, amount: int, slot: int) -> FundingGraphEvidence:
    identity = {
        "chain": "solana:mainnet-beta",
        "native_amount": amount,
        "observed_slot": slot,
        "provenance": {"source": "rpc", "signature": f"sig-{slot}"},
        "schema_version": "funding_graph_evidence.v1",
        "source_wallet": source,
        "target_wallet": target,
        "transaction_signature": f"sig-{slot}",
    }
    return FundingGraphEvidence(
        **identity, evidence_id=deterministic_id("funding_graph_evidence", identity)
    )


def test_funding_edge_query_filters_relationships() -> None:
    ledger = EvidenceGroundingLedger()
    ingest_funding_graph_evidence(_evidence("W1", "W2", 100, 10), ledger)
    ingest_funding_graph_evidence(_evidence("W2", "W3", 25, 20), ledger)
    model = build_funding_graph_read_model(ledger)
    result = query_funding_edges(
        model,
        source_wallet=" W1 ",
        target_wallet="W2",
        chain="solana:mainnet-beta",
        min_native_amount=50,
        min_observed_slot=5,
        max_observed_slot=15,
    )
    assert len(result.rows) == 1
    assert result.rows[0].evidence.native_amount == 100
    assert query_funding_edges(model, min_native_amount=200).rows == ()
