from smart_money.application.solana_candidate_pipeline import (
    aggregate_balance_deltas,
    attribute_program,
    build_wallet_profile,
    dashboard_candidate_view,
    early_entry_bps,
    infer_direction,
    join_candidate_context,
    aggregate_token_lifecycle,
    build_candidate_confidence,
    batch_wallet_capture,
    discover_token_mints,
    fetch_token_safety,
    extract_funding_transfers,
    calibrate_confidence,
    rank_smart_money_profiles,
)


def test_candidate_pipeline_aggregation_profile_ranking():
    assert aggregate_balance_deltas(({"owner": "w", "mint": "m", "delta": 2}, {"owner": "w", "mint": "m", "delta": -1})) == {"w:m": 1}
    assert attribute_program("jupiter") == "JUPITER"
    profile = build_wallet_profile("w", ({"direction": "BUY"}, {"direction": "SELL"}))
    assert profile.buy_count == 1
    assert rank_smart_money_profiles((profile,))[0] == profile
    assert dashboard_candidate_view((profile,))["read_only"] is True
    assert infer_direction(-10, 5) == "BUY"
    assert early_entry_bps(10, 10) == 10000
    assert join_candidate_context(profile, safety_status="SAFE", funding_links=1)["funding_links"] == 1
    assert aggregate_token_lifecycle(({"mint": "M", "slot": 9}, {"mint": "M", "slot": 7}))['M']["first_slot"] == 7
    assert build_candidate_confidence(early_entry=10000, safety_ok=True, funding_links=1) > 0
    assert batch_wallet_capture(("b", "a"), lambda wallet: wallet) == {"a": "a", "b": "b"}
    assert discover_token_mints(({"mint": "M"}, {"mint": "N"})) == ("M", "N")
    assert fetch_token_safety("M", lambda mint: {"mint": mint})["mint"] == "M"
    assert extract_funding_transfers(({"from": "F", "to": "W"},), "W") == ("F",)
    assert calibrate_confidence((10000, 0), (True, False)) == 10000
