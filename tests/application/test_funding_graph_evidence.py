from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.funding_graph_evidence import (
    FundingGraphEvidence,
    ingest_funding_graph_evidence,
)
from smart_money.core.ids import deterministic_id


def test_funding_graph_evidence_is_deterministic_and_idempotent() -> None:
    identity = {
        "chain": "solana:mainnet-beta",
        "native_amount": 100,
        "observed_slot": 42,
        "provenance": {"source": "rpc", "signature": "sig-1"},
        "schema_version": "funding_graph_evidence.v1",
        "source_wallet": "W1",
        "target_wallet": "W2",
        "transaction_signature": "sig-1",
    }
    evidence = FundingGraphEvidence(
        **identity, evidence_id=deterministic_id("funding_graph_evidence", identity)
    )
    ledger = EvidenceGroundingLedger()
    first = ingest_funding_graph_evidence(evidence, ledger)
    second = ingest_funding_graph_evidence(evidence, ledger)
    assert first.evidence_id == second.evidence_id
    assert second.already_present is True
    assert ledger.get(first.evidence_id).data["funding_graph"]["source_wallet"] == "W1"
