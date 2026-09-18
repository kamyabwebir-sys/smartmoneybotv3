from smart_money.application.live_candidate_enrichment import (
    enrich_live_candidates,
    extract_funding_edges,
    materialize_funding_graph_evidence,
    normalize_solana_safety,
)


def safety(mint=None, freeze=None, supply="1000", amounts=("400", "100")):
    return {
        "mint_account": {"result": {"value": {"data": {"parsed": {"info": {
            "mintAuthority": mint, "freezeAuthority": freeze, "supply": supply,
        }}}}}},
        "largest_accounts": {"result": {"value": [{"amount": amount} for amount in amounts]}},
    }


def transaction(signature="sig", wallet="target"):
    return {"result": {"slot": 9, "transaction": {"signatures": [signature], "message": {"instructions": [
        {"program": "system", "parsed": {"type": "transfer", "info": {"source": "funder", "destination": wallet, "lamports": 42}}},
    ]}}, "meta": {"innerInstructions": []}}}


def test_safety_and_funding_are_evidence_first_and_do_not_change_score():
    normalized = normalize_solana_safety(safety())
    assert normalized["top_accounts_concentration_bps"] == 5000
    edges = extract_funding_edges((transaction(),), "target")
    rows = enrich_live_candidates(
        [{"wallet": "target", "mint": "mint", "score_bps": 8123}],
        {"mint": safety()}, edges,
    )
    assert rows[0]["score_bps"] == 8123
    assert rows[0]["ranking_score_unchanged"]
    assert rows[0]["safety_status"] == "EVIDENCE_COMPLETE"
    assert rows[0]["funding_status"] == "VERIFIED"
    assert rows[0]["funding_edge_ids"]
    assert rows[0]["funding_evidence"][0]["chain"] == "solana:mainnet-beta"
    assert materialize_funding_graph_evidence(edges)[0].native_amount == 42


def test_missing_or_risky_safety_never_becomes_pass():
    rows = enrich_live_candidates(
        [{"wallet": "target", "mint": "missing"}, {"wallet": "target", "mint": "risky"}],
        {"risky": safety(mint="authority")}, (),
    )
    assert [row["safety_status"] for row in rows] == ["INCOMPLETE", "RISK_PRESENT"]
    assert all(row["funding_status"] == "NOT_OBSERVED" for row in rows)


def test_internal_and_unrelated_transfers_are_not_funding_edges():
    own = transaction("own", "target")
    own["result"]["transaction"]["message"]["instructions"][0]["parsed"]["info"]["source"] = "target"
    assert extract_funding_edges((own, transaction("other", "other-wallet")), "target") == ()
