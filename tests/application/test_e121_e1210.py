from smart_money.application.activity_intelligence import (
    build_readiness_gate, decode_pre_post_token_balances, detect_early_entry,
    detect_wash_or_self_route, enrich_activity, extract_pool_route,
    infer_buy_sell, project_activity_evidence, query_activity,
    rank_activity_candidates, verify_activity_replay,
)


def test_activity_intelligence_pipeline() -> None:
    assert decode_pre_post_token_balances({"w": 1}, {"w": 4})[0]["delta"] == 3
    assert infer_buy_sell(3) == "BUY"
    route = extract_pool_route("pool", ("raydium", "token"))
    assert not detect_wash_or_self_route("wallet", route.route)[0]
    enrichment = enrich_activity("wallet", "token", "BUY", route.pool_id)
    payload = project_activity_evidence(enrichment, 10)
    assert verify_activity_replay(payload, payload)
    assert detect_early_entry(5, 5)
    assert rank_activity_candidates(({"wallet": "wallet", "token": "token", "score": 2},))[0].rank == 1
    assert query_activity(({"wallet": "wallet", "token": "token"},), wallet="wallet")
    assert build_readiness_gate(("decode",), ("decode",)).ready
