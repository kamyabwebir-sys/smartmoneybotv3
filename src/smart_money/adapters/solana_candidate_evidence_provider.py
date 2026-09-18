"""Read-only Solana RPC projections for outcome and candidate safety evidence."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from smart_money.application.candidate_safety_funding_gate import (
    HolderConcentrationEvidence,
    LiquidityPoolEvidence,
    TokenAuthorityEvidence,
)
from smart_money.application.point_in_time_outcome import (
    PointInTimePriceEvidence,
    build_point_in_time_price_evidence,
)
from smart_money.core.ids import deterministic_id

RPC = Callable[[str, list[Any]], Mapping[str, Any]]


def _result(response: Mapping[str, Any]) -> Any:
    if not isinstance(response, Mapping) or "error" in response:
        raise ValueError("provider response is invalid")
    return response.get("result")


class SolanaCandidateEvidenceProvider:
    """Translate injected RPC responses into deterministic application evidence."""

    def __init__(self, request: RPC, *, source_id: str = "solana-rpc") -> None:
        if not callable(request) or not source_id.strip():
            raise ValueError("request and source_id are required")
        self._request = request
        self.source_id = source_id.strip()

    def authority(self, mint: str, *, observed_slot: int) -> TokenAuthorityEvidence:
        result = _result(
            self._request("getAccountInfo", [mint.strip(), {"encoding": "jsonParsed"}])
        )
        info = result.get("value", {}).get("data", {}).get("parsed", {}).get("info", {})
        if not isinstance(info, Mapping):
            raise TypeError("mint authority response is incomplete")
        identity = {
            "freeze_authority": info.get("freezeAuthority"),
            "mint": mint.strip(),
            "mint_authority": info.get("mintAuthority"),
            "observed_slot": observed_slot,
            "schema_version": "token_authority_evidence.v1",
            "source_id": self.source_id,
        }
        return TokenAuthorityEvidence(
            mint=identity["mint"],
            mint_authority=identity["mint_authority"],
            freeze_authority=identity["freeze_authority"],
            observed_slot=observed_slot,
            source_id=self.source_id,
            evidence_id=deterministic_id("token-authority-evidence", identity),
        )

    def holder_distribution(
        self, mint: str, *, observed_slot: int, supply_raw: int
    ) -> HolderConcentrationEvidence:
        if isinstance(supply_raw, bool) or not isinstance(supply_raw, int) or supply_raw <= 0:
            raise ValueError("supply_raw must be a positive integer")
        rows = _result(self._request("getTokenLargestAccounts", [mint.strip()]))
        values = rows.get("value") if isinstance(rows, Mapping) else None
        if not isinstance(values, Sequence):
            raise TypeError("holder response is incomplete")
        amounts = tuple(int(row["amount"]) for row in values if isinstance(row, Mapping))
        identity = {
            "holder_count": len(amounts),
            "mint": mint.strip(),
            "observed_slot": observed_slot,
            "schema_version": "holder_concentration_evidence.v1",
            "source_id": self.source_id,
            "top_holders_bps": min(10000, sum(amounts) * 10000 // supply_raw),
        }
        return HolderConcentrationEvidence(
            mint=identity["mint"],
            top_holders_bps=identity["top_holders_bps"],
            holder_count=identity["holder_count"],
            observed_slot=observed_slot,
            source_id=self.source_id,
            evidence_id=deterministic_id("holder-concentration-evidence", identity),
        )

    def pool_reserves(
        self,
        *,
        mint: str,
        pool: str,
        quote_mint: str,
        base_reserve_raw: int,
        quote_reserve_raw: int,
        observed_slot: int,
    ) -> LiquidityPoolEvidence:
        identity = {
            "base_reserve_raw": base_reserve_raw,
            "mint": mint.strip(),
            "observed_slot": observed_slot,
            "pool": pool.strip(),
            "quote_mint": quote_mint.strip(),
            "quote_reserve_raw": quote_reserve_raw,
            "schema_version": "liquidity_pool_evidence.v1",
            "source_id": self.source_id,
        }
        return LiquidityPoolEvidence(
            mint=identity["mint"], pool=identity["pool"],
            quote_mint=identity["quote_mint"], base_reserve_raw=base_reserve_raw,
            quote_reserve_raw=quote_reserve_raw, observed_slot=observed_slot,
            source_id=self.source_id,
            evidence_id=deterministic_id("liquidity-pool-evidence", identity),
        )

    def point_in_time_price(
        self,
        *,
        mint: str,
        quote_mint: str,
        observed_at: int,
        slot: int,
        asset_amount_raw: int,
        quote_value_raw: int,
    ) -> PointInTimePriceEvidence:
        return build_point_in_time_price_evidence(
            mint=mint, quote_mint=quote_mint, observed_at=observed_at, slot=slot,
            asset_amount_raw=asset_amount_raw, quote_value_raw=quote_value_raw,
            source_id=self.source_id,
        )


__all__ = ["SolanaCandidateEvidenceProvider"]
