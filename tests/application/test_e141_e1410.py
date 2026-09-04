from smart_money.application.production_candidate_engine import (
    adapt_rpc_transaction, bind_pool_liquidity, build_candidate_dashboard,
    build_funding_provenance, build_wash_trade_confidence, consolidate_candidate_features,
    consolidate_directions, early_entry_consistency, project_candidate_features,
    replay_candidate_ranking, resolve_balance_accounts,
)


def test_production_candidate_engine() -> None:
    assert adapt_rpc_transaction({"result": {"slot": 4}})["slot"] == 4
    assert resolve_balance_accounts(("a",), ({"post": 2},))[0]["account"] == "a"
    assert consolidate_directions(({"direction": "BUY"},))["BUY"] == 1
    context = bind_pool_liquidity("pool", 10, 15)
    assert context.context_id
    assert build_funding_provenance("wallet", ("fund",)).provenance_id
    assert early_entry_consistency((1, 3), (2, 2)) == 5000
    assert build_wash_trade_confidence("wallet", 2000, "route").evidence_id
    feature = consolidate_candidate_features("wallet", "token", {"BUY": 2, "SELL": 1}, 8000, 5)
    assert replay_candidate_ranking((feature,))[0] == feature
    assert build_candidate_dashboard((feature,))["rows"]
    assert project_candidate_features(feature, 10).evidence_type == "candidate_features"
