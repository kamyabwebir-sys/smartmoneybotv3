"""Exact, integer-only swap attribution from verified account and route evidence."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from smart_money.application.solana_account_resolution import resolve_solana_accounts
from smart_money.application.solana_wallet_token_activity import (
    SolanaWalletTokenActivityEvidence,
)
from smart_money.application.verified_swap_legs import verify_swap_legs
from smart_money.application.wallet_route_evidence import project_wallet_route
from smart_money.core.ids import deterministic_id

WRAPPED_SOL = "So11111111111111111111111111111111111111112"
QUOTE_MINTS = frozenset(
    {
        WRAPPED_SOL,
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    }
)


@dataclass(frozen=True, slots=True)
class ExactSwapAttribution:
    signature: str
    slot: int
    wallet: str
    direction: str
    quote_mint: str
    asset_mint: str
    quote_amount_raw: int
    asset_amount_raw: int
    pools: tuple[str, ...]
    mint_path: tuple[str, ...]
    account_resolution_id: str
    route_evidence_id: str
    wash_trade_confidence_bps: int
    suppressed: bool
    suppression_reasons: tuple[str, ...]
    attribution_id: str
    schema_version: str = "exact_swap_attribution.v1"

    def __post_init__(self) -> None:
        if self.direction not in {"BUY", "SELL"}:
            raise ValueError("exact attribution direction must be BUY or SELL")
        for name in (
            "signature",
            "wallet",
            "quote_mint",
            "asset_mint",
            "account_resolution_id",
            "route_evidence_id",
            "attribution_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        for name in ("slot", "quote_amount_raw", "asset_amount_raw"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if not self.quote_amount_raw or not self.asset_amount_raw:
            raise ValueError("exact attributed amounts must be positive")
        if self.quote_mint == self.asset_mint:
            raise ValueError("quote and asset mints must differ")
        if not self.pools or not self.mint_path:
            raise ValueError("pool and mint paths must be non-empty")
        if not 0 <= self.wash_trade_confidence_bps <= 10000:
            raise ValueError("wash_trade_confidence_bps must be 0..10000")
        if self.suppressed != bool(self.suppression_reasons):
            raise ValueError("suppression status must match suppression reasons")
        if self.attribution_id != deterministic_id(
            "exact-swap-attribution", self.identity_payload()
        ):
            raise ValueError("attribution_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, object]:
        return {
            "account_resolution_id": self.account_resolution_id,
            "asset_amount_raw": self.asset_amount_raw,
            "asset_mint": self.asset_mint,
            "direction": self.direction,
            "mint_path": self.mint_path,
            "pools": self.pools,
            "quote_amount_raw": self.quote_amount_raw,
            "quote_mint": self.quote_mint,
            "route_evidence_id": self.route_evidence_id,
            "schema_version": self.schema_version,
            "signature": self.signature,
            "slot": self.slot,
            "suppressed": self.suppressed,
            "suppression_reasons": self.suppression_reasons,
            "wallet": self.wallet,
            "wash_trade_confidence_bps": self.wash_trade_confidence_bps,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"attribution_id": self.attribution_id, **self.identity_payload()}


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def build_exact_swap_attribution(
    raw: Mapping[str, Any], wallet: str
) -> ExactSwapAttribution:
    if not isinstance(raw, Mapping):
        raise TypeError("raw transaction must be a mapping")
    if not isinstance(wallet, str) or not wallet.strip():
        raise ValueError("wallet must be non-empty")
    document = dict(raw)
    resolution = resolve_solana_accounts(document)
    canonical_wallet = wallet.strip()
    if canonical_wallet not in resolution.signers:
        raise ValueError("wallet signer is not established")
    route = project_wallet_route(document, canonical_wallet)
    swaps = verify_swap_legs(document, route)
    if route["gaps"] or swaps["unresolved"] or not swaps["legs"]:
        raise ValueError("route contains unresolved evidence")
    if route["native_delta_excluding_fee"] != 0:
        raise ValueError("native fee/rent corrected delta is unresolved")

    legs = tuple(swaps["legs"])
    for previous, current in pairwise(legs):
        if (
            previous["output_mint"] != current["input_mint"]
            or previous["destination"] != current["source"]
            or previous["amount_out_raw"] != current["amount_in_raw"]
        ):
            raise ValueError("swap route is disconnected")
    mint_path = (legs[0]["input_mint"],) + tuple(
        leg["output_mint"] for leg in legs
    )
    first, last = mint_path[0], mint_path[-1]
    if first in QUOTE_MINTS and last not in QUOTE_MINTS:
        direction, quote_mint, asset_mint = "BUY", first, last
        quote_amount = int(legs[0]["amount_in_raw"])
        asset_amount = int(legs[-1]["amount_out_raw"])
    elif first not in QUOTE_MINTS and last in QUOTE_MINTS:
        direction, quote_mint, asset_mint = "SELL", last, first
        quote_amount = int(legs[-1]["amount_out_raw"])
        asset_amount = int(legs[0]["amount_in_raw"])
    else:
        raise ValueError("quote/base endpoints are not exact")

    items = {item["mint"]: item for item in route["items"]}
    asset_item, quote_item = items.get(asset_mint), items.get(quote_mint)
    expected_asset_sign = 1 if direction == "BUY" else -1
    expected_quote_sign = -1 if direction == "BUY" else 1
    if asset_item is None or quote_item is None:
        raise ValueError("wallet endpoint balances are unavailable")
    if int(asset_item["raw_delta"]) * expected_asset_sign <= 0:
        raise ValueError("asset balance direction mismatch")
    if int(quote_item["raw_delta"]) * expected_quote_sign <= 0:
        raise ValueError("quote balance direction mismatch")

    reasons: list[str] = []
    wash_score = 0
    if len(set(mint_path)) != len(mint_path):
        reasons.append("CYCLIC_MINT_ROUTE")
        wash_score += 7500
    pools = tuple(str(leg["pool"]) for leg in legs)
    if len(set(pools)) != len(pools):
        reasons.append("REUSED_POOL_ROUTE")
        wash_score += 2500
    if first == last:
        reasons.append("SELF_RETURN_ROUTE")
        wash_score = 10000
    wash_score = min(10000, wash_score)
    identity = {
        "account_resolution_id": resolution.resolution_id,
        "asset_amount_raw": _integer(asset_amount, "asset_amount_raw"),
        "asset_mint": asset_mint,
        "direction": direction,
        "mint_path": mint_path,
        "pools": pools,
        "quote_amount_raw": _integer(quote_amount, "quote_amount_raw"),
        "quote_mint": quote_mint,
        "route_evidence_id": route["evidence_id"],
        "schema_version": "exact_swap_attribution.v1",
        "signature": route["signature"],
        "slot": _integer(document.get("slot"), "slot"),
        "suppressed": bool(reasons),
        "suppression_reasons": tuple(reasons),
        "wallet": canonical_wallet,
        "wash_trade_confidence_bps": wash_score,
    }
    return ExactSwapAttribution(
        attribution_id=deterministic_id("exact-swap-attribution", identity),
        **identity,
    )


def project_exact_attribution_activity(
    attribution: ExactSwapAttribution,
) -> SolanaWalletTokenActivityEvidence:
    if not isinstance(attribution, ExactSwapAttribution):
        raise TypeError("attribution must be ExactSwapAttribution")
    if attribution.suppressed:
        raise ValueError("suppressed attribution cannot enter intelligence")
    token_delta = (
        attribution.asset_amount_raw
        if attribution.direction == "BUY"
        else -attribution.asset_amount_raw
    )
    identity = {
        "direction": attribution.direction,
        "mint": attribution.asset_mint,
        "native_delta": 0,
        "schema_version": "solana_wallet_token_activity.v1",
        "slot": attribution.slot,
        "token_delta": token_delta,
        "transaction_signature": attribution.signature,
        "wallet": attribution.wallet,
    }
    return SolanaWalletTokenActivityEvidence(
        activity_id=deterministic_id("solana_wallet_token_activity", identity),
        **identity,
    )


__all__ = [
    "ExactSwapAttribution",
    "build_exact_swap_attribution",
    "project_exact_attribution_activity",
]
