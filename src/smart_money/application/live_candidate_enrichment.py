"""Pure evidence enrichment for live candidates; never changes ranking scores."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def normalize_solana_safety(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise TypeError("safety provider response must be a mapping")
    mint_response, holders_response = raw.get("mint_account"), raw.get("largest_accounts")
    try:
        info = mint_response["result"]["value"]["data"]["parsed"]["info"]
        values = holders_response["result"]["value"]
        supply = int(info["supply"])
        concentrations = [int(item["amount"]) for item in values]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("incomplete token safety RPC evidence") from exc
    concentration_bps = sum(concentrations) * 10000 // supply if supply > 0 else None
    mint_authority = info.get("mintAuthority")
    freeze_authority = info.get("freezeAuthority")
    complete = concentration_bps is not None
    return {
        "schema_version": "solana_rpc_token_safety.v1",
        "mint_authority": mint_authority,
        "freeze_authority": freeze_authority,
        "top_accounts_concentration_bps": concentration_bps,
        "authority_risk_observed": mint_authority is not None or freeze_authority is not None,
        "complete": complete,
        "source": "solana_rpc:getAccountInfo+getTokenLargestAccounts",
    }


def extract_funding_edges(transaction_responses: tuple[Mapping[str, Any], ...], wallet: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(wallet, str) or not wallet.strip():
        raise ValueError("wallet must be non-empty")
    edges: dict[tuple[str, str], dict[str, Any]] = {}
    for response in transaction_responses:
        try:
            result = response["result"]
            signature = result["transaction"]["signatures"][0]
            slot = result["slot"]
            outer = result["transaction"]["message"].get("instructions", [])
            inner = [item for group in result.get("meta", {}).get("innerInstructions", []) for item in group.get("instructions", [])]
        except (KeyError, TypeError, IndexError):
            continue
        for instruction in (*outer, *inner):
            parsed = instruction.get("parsed") if isinstance(instruction, Mapping) else None
            if instruction.get("program") != "system" or not isinstance(parsed, Mapping) or parsed.get("type") not in {"transfer", "transferWithSeed"}:
                continue
            info = parsed.get("info")
            if not isinstance(info, Mapping):
                continue
            source, target, lamports = info.get("source"), info.get("destination"), info.get("lamports")
            if target != wallet or source == wallet or not isinstance(source, str) or type(lamports) is not int or lamports <= 0:
                continue
            key = (signature, source)
            edges[key] = {"source_wallet": source, "target_wallet": wallet, "native_amount": lamports,
                          "slot": slot, "signature": signature, "source": "solana_rpc:parsed_system_transfer"}
    return tuple(edges[key] for key in sorted(edges))


def enrich_live_candidates(
    ranking: list[dict[str, Any]],
    safety_by_mint: Mapping[str, Mapping[str, Any]],
    funding_edges: tuple[dict[str, Any], ...],
) -> list[dict[str, Any]]:
    enriched = []
    for original in ranking:
        row = dict(original)
        mint = row.get("mint")
        raw_safety = safety_by_mint.get(mint) if isinstance(mint, str) else None
        try:
            safety = normalize_solana_safety(raw_safety) if raw_safety is not None else None
        except (TypeError, ValueError):
            safety = None
        if safety is None:
            safety_status = "INCOMPLETE"
        elif safety["authority_risk_observed"]:
            safety_status = "RISK_PRESENT"
        else:
            safety_status = "EVIDENCE_COMPLETE"
        wallet = row.get("wallet")
        related = tuple(edge for edge in funding_edges if edge["target_wallet"] == wallet)
        row.update(
            safety_status=safety_status,
            safety_evidence=safety,
            funding_status="VERIFIED" if related else "NOT_OBSERVED",
            funding_evidence=related,
            ranking_score_unchanged=True,
        )
        enriched.append(row)
    return enriched


__all__ = ["enrich_live_candidates", "extract_funding_edges", "normalize_solana_safety"]
