"""Pure evidence enrichment for live candidates; never changes ranking scores."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from smart_money.application.funding_graph_evidence import FundingGraphEvidence
from smart_money.core.ids import deterministic_id


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


def extract_funding_edges(
    transaction_responses: tuple[Mapping[str, Any], ...],
    wallet: str,
    *,
    token_account_owners: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Extract inbound native and SPL funding transfers for one wallet.

    Native System Program transfers and parsed SPL Token transfers
    (transfer/transferChecked) are both accepted. For SPL transfers the
    destination is a token account, so ownership must be proven via the
    ``token_account_owners`` mapping (account → owner) or an explicit
    ``owner``/``authority`` field in the parsed info; otherwise the edge is
    rejected fail-closed. Self-routed transfers, unproven ownership, unknown
    mint/scheme payloads and non-positive amounts never become edges.
    """
    if not isinstance(wallet, str) or not wallet.strip():
        raise ValueError("wallet must be non-empty")
    owners = token_account_owners or {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
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
            if not isinstance(instruction, Mapping):
                continue
            parsed = instruction.get("parsed")
            if not isinstance(parsed, Mapping):
                continue
            info = parsed.get("info")
            if not isinstance(info, Mapping):
                continue
            program = instruction.get("program")
            transfer_type = parsed.get("type")
            if program == "system" and transfer_type in {"transfer", "transferWithSeed"}:
                source, target = info.get("source"), info.get("destination")
                amount, mint = info.get("lamports"), "native"
                provenance = "solana_rpc:parsed_system_transfer"
            elif program == "spl-token" and transfer_type in {"transfer", "transferChecked"}:
                source, target = info.get("source"), info.get("destination")
                amount, mint = info.get("amount"), info.get("mint")
                provenance = "solana_rpc:parsed_spl_token_transfer"
            else:
                continue
            if program == "spl-token":
                # Destination is a token account: prove it is owned by wallet.
                payload_owner = info.get("owner") or info.get("authority")
                payload_owner = payload_owner.strip() if isinstance(payload_owner, str) else ""
                resolved = owners.get(target, "").strip() if isinstance(target, str) else ""
                proven_owner = wallet in {payload_owner, resolved}
                if not proven_owner and target != wallet:
                    continue  # unproven ownership fails closed
            elif target != wallet:
                continue
            if source == wallet or not isinstance(source, str):
                continue
            # Accept plain ints and unsigned digit strings (RPC JSON format);
            # everything else (bool, float, signed, decimal text) fails closed.
            if isinstance(amount, str):
                if not amount.isdigit():
                    continue
                amount = int(amount)
            if type(amount) is not int or amount <= 0:
                continue
            if not isinstance(mint, str) or not mint.strip():
                continue
            key = (signature, source, mint)
            edges[key] = {"source_wallet": source, "target_wallet": wallet, "mint": mint,
                          "amount": amount, "slot": slot, "signature": signature,
                          "source": provenance}
    return tuple(edges[key] for key in sorted(edges))


def materialize_funding_graph_evidence(
    funding_edges: tuple[Mapping[str, Any], ...],
) -> tuple[FundingGraphEvidence, ...]:
    """Convert parsed inbound transfers (native or SPL) into canonical evidence."""
    evidence: dict[str, FundingGraphEvidence] = {}
    for edge in funding_edges:
        identity = {
            "chain": "solana:mainnet-beta",
            "native_amount": edge.get("amount", edge.get("native_amount")),
            "observed_slot": edge.get("slot"),
            "provenance": {"source": str(edge.get("source", "")).strip()},
            "schema_version": "funding_graph_evidence.v1",
            "source_wallet": str(edge.get("source_wallet", "")).strip(),
            "target_wallet": str(edge.get("target_wallet", "")).strip(),
            "transaction_signature": str(edge.get("signature", "")).strip(),
        }
        item = FundingGraphEvidence(
            **identity,
            evidence_id=deterministic_id("funding_graph_evidence", identity),
        )
        evidence[item.evidence_id] = item
    return tuple(evidence[key] for key in sorted(evidence))


def enrich_live_candidates(
    ranking: list[dict[str, Any]],
    safety_by_mint: Mapping[str, Mapping[str, Any]],
    funding_edges: tuple[dict[str, Any], ...],
) -> list[dict[str, Any]]:
    canonical_funding = materialize_funding_graph_evidence(funding_edges)
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
        related = tuple(
            edge for edge in canonical_funding if edge.target_wallet == wallet
        )
        row.update(
            safety_status=safety_status,
            safety_evidence=safety,
            funding_status="VERIFIED" if related else "NOT_OBSERVED",
            funding_evidence=tuple(edge.canonical_dict() for edge in related),
            funding_edge_ids=tuple(edge.evidence_id for edge in related),
            ranking_score_unchanged=True,
        )
        enriched.append(row)
    return enriched


__all__ = [
    "enrich_live_candidates",
    "extract_funding_edges",
    "materialize_funding_graph_evidence",
    "normalize_solana_safety",
]
