from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.production_discovery import (
    classify_program_swap, extract_rpc_balances, fetch_transaction_batch,
    project_early_entry, project_token_activity, project_wallet_activity,
    project_wash_trade, rank_production_candidates, resolve_pool_route,
    verify_production_discovery_gate,
)


def test_production_discovery_pipeline() -> None:
    assert fetch_transaction_batch(lambda sig: {"signature": sig}, ("a",))[0]["signature"] == "a"
    assert extract_rpc_balances({"result": {"balances": {"w": {"pre": 1, "post": 3}}}})[0]["delta"] == 2
    assert classify_program_swap("jupiter", {"type": "SWAP"}) == "JUPITER_SWAP"
    assert resolve_pool_route("pool", ("a", "b")).resolution_id
    ledger = EvidenceGroundingLedger()
    assert project_wallet_activity(ledger, "w", "t", 1, 2)
    assert project_token_activity(ledger, "t", "w", 1, 2)
    assert project_early_entry("w", "t", 1, 2).evidence_type == "early_entry_evidence"
    assert project_wash_trade("w", ("w", "p")).data["detected"]
    assert rank_production_candidates(({"wallet": "w", "score": 4},))[0]["rank"] == 1
    assert verify_production_discovery_gate(("decode",), ("decode",))
