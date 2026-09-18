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


def spl_transaction(signature="spl-sig", wallet="target", amount="5000", mint="USDC-mint", transfer_type="transferChecked", inner=False):
    instruction = {
        "program": "spl-token",
        "parsed": {"type": transfer_type, "info": {
            "source": "funder-ata", "destination": "target-ata", "amount": amount, "mint": mint,
        }},
    }
    body = {"result": {"slot": 11, "transaction": {"signatures": [signature], "message": {"instructions": []}}, "meta": {"innerInstructions": []}}}
    if inner:
        body["result"]["meta"]["innerInstructions"] = [{"instructions": [instruction]}]
    else:
        body["result"]["transaction"]["message"]["instructions"] = [instruction]
    return body


OWNERS = {"target-ata": "target"}


def test_spl_token_transfer_checked_inbound_is_a_funding_edge():
    edges = extract_funding_edges((spl_transaction(),), "target", token_account_owners=OWNERS)
    assert len(edges) == 1
    edge = edges[0]
    assert edge["source_wallet"] == "funder-ata"
    assert edge["target_wallet"] == "target"
    assert edge["mint"] == "USDC-mint"
    assert edge["amount"] == 5000
    assert edge["source"] == "solana_rpc:parsed_spl_token_transfer"
    evidence = materialize_funding_graph_evidence(edges)[0]
    assert evidence.native_amount == 5000
    assert evidence.source_wallet == "funder-ata"


def test_spl_transfer_without_checked_variant_is_accepted():
    edges = extract_funding_edges((spl_transaction(transfer_type="transfer"),), "target", token_account_owners=OWNERS)
    assert edges[0]["amount"] == 5000


def test_spl_transfer_inside_inner_instructions_is_found():
    edges = extract_funding_edges((spl_transaction(inner=True),), "target", token_account_owners=OWNERS)
    assert len(edges) == 1


def test_spl_funding_edges_are_deduplicated_per_signature_source_mint():
    edges = extract_funding_edges((spl_transaction(), spl_transaction()), "target", token_account_owners=OWNERS)
    assert len(edges) == 1


def test_unproven_spl_destination_ownership_fails_closed():
    """No owner map and no owner field: the edge must NOT be trusted."""
    assert extract_funding_edges((spl_transaction(),), "target") == ()
    assert extract_funding_edges((spl_transaction(),), "target", token_account_owners={"other-ata": "target"}) == ()


def test_payload_owner_field_proves_ownership_without_map():
    payload = spl_transaction()
    payload["result"]["transaction"]["message"]["instructions"][0]["parsed"]["info"]["owner"] = "target"
    edges = extract_funding_edges((payload,), "target")
    assert len(edges) == 1


def test_malformed_spl_payloads_fail_closed_without_crashing():
    variants = (
        spl_transaction(amount="-5"),
        spl_transaction(amount=0),
        spl_transaction(amount=None),
        spl_transaction(amount="12.5"),
        spl_transaction(mint=""),
        spl_transaction(mint=None),
        spl_transaction(mint=42),
        spl_transaction(wallet="someone-else"),  # destination proves another wallet
    )
    assert extract_funding_edges(variants, "target", token_account_owners={"other-ata": "target"}) == ()


def test_self_funded_spl_transfer_is_not_a_funding_edge():
    own = spl_transaction()
    own["result"]["transaction"]["message"]["instructions"][0]["parsed"]["info"]["source"] = "target"
    assert extract_funding_edges((own,), "target", token_account_owners=OWNERS) == ()


def test_native_and_spl_edges_from_same_signature_are_distinct():
    combined = (
        transaction("mixed-sig"),
        spl_transaction(signature="mixed-sig"),
    )
    edges = extract_funding_edges(combined, "target", token_account_owners=OWNERS)
    assert len(edges) == 2
    evidence = materialize_funding_graph_evidence(edges)
    assert {item.native_amount for item in evidence} == {42, 5000}


def test_spl_funding_binds_to_candidate_without_changing_score():
    edges = extract_funding_edges((spl_transaction(),), "target", token_account_owners=OWNERS)
    rows = enrich_live_candidates(
        [{"wallet": "target", "mint": "mint", "score_bps": 7000}],
        {}, edges,
    )
    assert rows[0]["score_bps"] == 7000
    assert rows[0]["funding_status"] == "VERIFIED"
    assert rows[0]["funding_evidence"][0]["chain"] == "solana:mainnet-beta"
