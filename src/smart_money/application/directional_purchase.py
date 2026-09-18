"""Observed USDC-funded purchase, not investment quality or full Jupiter decoding.

Positive scope: one Jupiter invocation, supported exact-input Raydium legs,
pre-existing token accounts, strictly reconciled fee-free SPL movements, no
native movement beyond the fee. Pool historical state is NOT certified here.
"""
import hashlib
import json
from itertools import pairwise

from smart_money.application.solana_candidate_pipeline import (
    rank_wallet_token_candidates,
)
from smart_money.application.verified_swap_legs import (
    AMM,
    CLMM,
    CPMM,
    _check_transfer_balances,
    verify_swap_legs,
)
from smart_money.application.wallet_route_evidence import (
    TOKEN_PROGRAMS,
    project_wallet_route,
)
from smart_money.core.ids import deterministic_id

JUPITER = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
COMPUTE_BUDGET = "ComputeBudget111111111111111111111111111111"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def evaluate_directional_purchase(raw: dict, wallet: str) -> dict:
    route = project_wallet_route(raw, wallet)
    swaps = verify_swap_legs(raw, route)
    decision = {"schema_version": "observed_directional_purchase.v1", "wallet": wallet,
                "source_result_sha256": hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
                "signature": route["signature"], "route_evidence_id": route["evidence_id"],
                "accepted": False, "reason": "unsupported_or_incomplete_purchase",
                "mint": None, "human_review_required": True,
                "historical_pool_state_verified": False,
                "full_jupiter_instruction_decoded": False}
    try:
        _verify_purchase(raw, route, swaps, decision)
    except ValueError as exc:
        decision["reason"] = str(exc)
    decision["evidence_id"] = deterministic_id("observed_directional_purchase", decision)
    return {"route": route, "swaps": swaps, "purchase": decision}


def _verify_purchase(raw: dict, route: dict, swaps: dict, decision: dict) -> None:
    wallet, meta = route["wallet"], raw["meta"]
    keys = raw["transaction"]["message"]["accountKeys"]
    if not any(isinstance(k, dict) and k.get("pubkey") == wallet and k.get("signer") is True for k in keys):
        raise ValueError("wallet_signer_not_established")
    if route["gaps"] or swaps["unresolved"] or not swaps["legs"]:
        raise ValueError("unresolved_transfers_or_swap_legs")
    if route["native_delta_excluding_fee"] != 0 or meta["preBalances"][1:] != meta["postBalances"][1:]:
        raise ValueError("native_or_rent_movement_not_supported")
    top = raw["transaction"]["message"]["instructions"]
    outer_indices = [n for n, i in enumerate(top) if i.get("programId") == JUPITER]
    if len(outer_indices) != 1 or any(i.get("programId") not in {JUPITER, COMPUTE_BUDGET} for i in top):
        raise ValueError("unsupported_outer_program")
    outer = outer_indices[0]
    allowed = TOKEN_PROGRAMS | {JUPITER, COMPUTE_BUDGET, CPMM, AMM, CLMM}
    for invocation in route["program_invocations"]:
        if invocation["program"] not in allowed:
            raise ValueError("unknown_program_in_route")
    instructions = [top[outer]] + next(g["instructions"] for g in meta["innerInstructions"] if g["index"] == outer)
    for ins in instructions[1:]:
        if ins.get("programId") in TOKEN_PROGRAMS and ins.get("parsed", {}).get("type") not in {"transfer", "transferChecked"}:
            raise ValueError("unsupported_token_operation")
    _check_transfer_balances(raw, route)
    legs = swaps["legs"]
    if any(leg["outer"] != outer or instructions[leg["position"]].get("stackHeight") != 2 for leg in legs):
        raise ValueError("unsupported_route_nesting")
    edges = {(e["outer"], e["position"]): e for e in route["transfers"]}
    used = set()
    for leg in legs:
        left_key, right_key = (outer, leg["input_transfer_position"]), (outer, leg["output_transfer_position"])
        left, right = edges[left_key], edges[right_key]
        if left["source_owner"] != wallet or right["destination_owner"] != wallet or left["destination_owner"] == wallet or right["source_owner"] == wallet:
            raise ValueError("swap_not_owned_by_wallet")
        used.update((left_key, right_key))
    for before, after in pairwise(legs):
        if (before["output_mint"], before["destination"], before["amount_out_raw"]) != (after["input_mint"], after["source"], after["amount_in_raw"]):
            raise ValueError("disconnected_swap_legs")
    mint_path = [legs[0]["input_mint"]] + [leg["output_mint"] for leg in legs]
    if len(set(mint_path)) != len(mint_path) or mint_path[0] != USDC:
        raise ValueError("cyclic_or_non_usdc_route")
    items = {row["mint"]: row for row in route["items"]}
    first, last = items.get(USDC), items.get(mint_path[-1])
    if first is None or last is None or first["classification"] != "NET_OUTFLOW" or last["classification"] != "NET_INFLOW":
        raise ValueError("not_directional_owner_flow")
    if first["decimals"] != 6:
        raise ValueError("invalid_usdc_decimals")
    if int(last["raw_delta"]) != int(legs[-1]["amount_out_raw"]):
        raise ValueError("output_balance_mismatch")
    if any(int(item["raw_delta"]) != 0 for mint, item in items.items() if mint not in {USDC, mint_path[-1]}):
        raise ValueError("unexplained_other_asset_change")
    auxiliary = 0
    for key, edge in edges.items():
        if key in used:
            continue
        # Account for auxiliary quote spending; do not invent its recipient's purpose.
        if edge["mint"] != USDC or edge["source"] != legs[0]["source"] or edge["source_owner"] != wallet or edge["destination_owner"] == wallet or key[0] != outer or instructions[key[1]].get("stackHeight") != 2:
            raise ValueError("unexplained_transfer")
        auxiliary += int(edge["raw_amount"])
    spent = -int(first["raw_delta"])
    if spent != int(legs[0]["amount_in_raw"]) + auxiliary:
        raise ValueError("quote_spend_mismatch")
    decision.update(accepted=True, reason="observed_acyclic_usdc_funded_purchase",
                    mint=mint_path[-1], quote_mint=USDC, quote_spent_raw=str(spent),
                    quote_decimals=first["decimals"], amount_received_raw=last["raw_delta"],
                    token_decimals=last["decimals"], auxiliary_quote_outflow_raw=str(auxiliary),
                    mint_path=mint_path)


def rank_purchase_evaluations(evaluations: list[dict]) -> list[dict]:
    """One score per transaction/token. Scores are ordering weights, not confidence."""
    rows = []
    for evaluation in evaluations:
        route, decision = evaluation["route"], evaluation["purchase"]
        for item in route["items"]:
            eligible = decision["accepted"] and item["mint"] == decision["mint"]
            row = dict(item, wallet=route["wallet"], signature=route["signature"],
                       evidence_id=decision["evidence_id"], ranking_eligible=eligible,
                       directional_buy_verified=eligible, buy_count=int(eligible),
                       reason=decision["reason"] if eligible else "not_verified_directional_output",
                       score_kind="ordering_weight_not_probability")
            row = rank_wallet_token_candidates((row,))[0]
            row["ranking_score"] = row["score_bps"]
            rows.append(row)
    return sorted(rows, key=lambda row: (-row["score_bps"], row["wallet"], row["mint"], row["signature"]))
