"""Conservative transfer-flow evidence. Does not claim exact DEX pools or profit."""
from typing import Any

from smart_money.application.wallet_balance_reconciliation import reconcile_wallet_balances
from smart_money.application.solana_candidate_pipeline import rank_wallet_token_candidates
from smart_money.core.ids import deterministic_id

TOKEN_PROGRAMS = frozenset({"TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
                            "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"})


def project_wallet_route(raw: dict[str, Any], wallet: str) -> dict[str, Any]:
    balance = reconcile_wallet_balances(raw, wallet)
    meta, message = raw["meta"], raw["transaction"]["message"]
    keys = [k["pubkey"] if isinstance(k, dict) else k for k in message["accountKeys"]]
    accounts = {}
    for row in meta["preTokenBalances"] + meta["postTokenBalances"]:
        accounts[keys[row["accountIndex"]]] = (row["owner"], row["mint"], row["uiTokenAmount"]["decimals"])
    gaps, edges, programs = [], [], []
    top = message.get("instructions")
    if not isinstance(top, list):
        raise ValueError("instructions required")
    inner = meta.get("innerInstructions")
    if not isinstance(inner, list):
        gaps.append("inner_instructions_unavailable")
        inner = []
    groups = {}
    for group in inner:
        index = group.get("index")
        if type(index) is not int or not 0 <= index < len(top) or index in groups:
            raise ValueError("invalid inner instruction group")
        if not isinstance(group.get("instructions"), list):
            raise ValueError("invalid inner instructions")
        groups[index] = group["instructions"]
    for outer, instruction in enumerate(top):
        for position, ins in enumerate([instruction] + groups.get(outer, [])):
            program = ins.get("programId")
            if not isinstance(program, str):
                gaps.append("unresolved_program")
                continue
            programs.append({"outer": outer, "position": position, "program": program})
            if program not in TOKEN_PROGRAMS:
                continue
            parsed = ins.get("parsed")
            if not isinstance(parsed, dict):
                gaps.append("unparsed_token_instruction")
                continue
            kind = parsed.get("type")
            if kind not in {"transfer", "transferChecked"}:
                if kind not in {"closeAccount", "initializeAccount", "initializeAccount2", "initializeAccount3", "syncNative"}:
                    gaps.append("unsupported_token_instruction")
                continue
            info = parsed.get("info", {})
            source, destination = info.get("source"), info.get("destination")
            left, right = accounts.get(source), accounts.get(destination)
            amount_info = info.get("tokenAmount", {}) if kind == "transferChecked" else info
            amount = amount_info.get("amount")
            if not isinstance(amount, str) or not amount or any(c not in "0123456789" for c in amount):
                raise ValueError("invalid transfer amount")
            if left is None or right is None:
                gaps.append("unresolved_transfer_account")
                continue
            if left[1:] != right[1:]:
                raise ValueError("transfer mint/decimals conflict")
            if kind == "transferChecked" and (info.get("mint") != left[1] or amount_info.get("decimals") != left[2]):
                raise ValueError("checked transfer identity conflict")
            edges.append({"outer": outer, "position": position, "source": source,
                          "destination": destination, "source_owner": left[0], "destination_owner": right[0],
                          "mint": left[1], "decimals": left[2], "raw_amount": amount})
    items = []
    for mint, decimals, delta in balance.token_deltas:
        incoming = sum(int(e["raw_amount"]) for e in edges if e["mint"] == mint and e["destination_owner"] == wallet and e["source_owner"] != wallet)
        outgoing = sum(int(e["raw_amount"]) for e in edges if e["mint"] == mint and e["source_owner"] == wallet and e["destination_owner"] != wallet)
        matched = incoming - outgoing == delta
        if not matched:
            gaps.append("transfer_balance_mismatch:" + mint)
        classification = "UNKNOWN"
        if matched and not gaps:
            if incoming and outgoing:
                classification = "INTERMEDIATE" if delta == 0 else "ROUND_TRIP_FLOW"
            elif incoming and delta > 0:
                classification = "NET_INFLOW"
            elif outgoing and delta < 0:
                classification = "NET_OUTFLOW"
            else:
                classification = "UNCHANGED"
        items.append({"mint": mint, "decimals": decimals, "raw_delta": str(delta),
                      "incoming_raw": str(incoming), "outgoing_raw": str(outgoing),
                      "classification": classification, "balance_matched": matched,
                      "directional_buy_verified": False, "ranking_eligible": False,
                      "ranking_score": 0, "reason": "swap_intent_not_verified"})
    if gaps:
        for item in items:
            item["classification"] = "UNKNOWN"
    result = {"schema_version": "wallet_route_evidence.v1", "wallet": wallet,
              "signature": balance.signature, "balance_evidence_id": balance.evidence_id,
              "native_delta_excluding_fee": balance.native_delta_excluding_fee,
              "transfers": edges, "program_invocations": programs, "items": items,
              "gaps": sorted(set(gaps)), "pool_resolution": "UNVERIFIED",
              "cycle_verified": False}
    result["evidence_id"] = deterministic_id("wallet_route_evidence", result)
    return result


def rank_directional_evidence(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """No transfer-only observation qualifies as a verified directional BUY."""
    rows = [dict(item, wallet=r["wallet"], evidence_id=r["evidence_id"])
            for r in reports for item in r["items"]]
    excluded = frozenset((r["wallet"], r["mint"]) for r in rows)
    return list(rank_wallet_token_candidates(tuple(rows), excluded_subjects=excluded))
