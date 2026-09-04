from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.funding_graph_evidence import FundingGraphEvidence, ingest_funding_graph_evidence
from smart_money.application.funding_graph_read_model import build_funding_graph_read_model
from smart_money.core.ids import deterministic_id


def test_funding_graph_read_model_reconstructs_edges() -> None:
    identity = {
        "chain": "solana:mainnet-beta", "native_amount": 100, "observed_slot": 42,
        "provenance": {"source": "rpc", "signature": "sig-1"},
        "schema_version": "funding_graph_evidence.v1", "source_wallet": "W1",
        "target_wallet": "W2", "transaction_signature": "sig-1",
    }
    evidence = FundingGraphEvidence(
        **identity, evidence_id=deterministic_id("funding_graph_evidence", identity)
    )
    ledger = EvidenceGroundingLedger()
    ingest_funding_graph_evidence(evidence, ledger)
    model = build_funding_graph_read_model(ledger)
    assert len(model.rows) == 1
    assert model.rows[0].evidence.source_wallet == "W1"
    assert model.rows[0].ledger_evidence_id == ledger.iter_payloads().__next__().get_canonical_id()
