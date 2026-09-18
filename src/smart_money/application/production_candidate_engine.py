from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload


def adapt_rpc_transaction(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping) or "result" not in raw:
        raise ValueError("RPC transaction must contain result")
    result = raw["result"]
    if not isinstance(result, Mapping):
        raise ValueError("RPC result must be mapping")
    return {"slot": int(result.get("slot", 0)), "meta": dict(result.get("meta") or {}),
            "transaction": dict(result.get("transaction") or {})}


def resolve_balance_accounts(accounts: tuple[str, ...], balances: tuple[Mapping[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    if len(accounts) != len(balances):
        raise ValueError("accounts and balances length mismatch")
    return tuple({"account": account, **dict(balance)} for account, balance in zip(accounts, balances))


def consolidate_directions(events: tuple[Mapping[str, Any], ...]) -> dict[str, int]:
    result = {"BUY": 0, "SELL": 0, "UNKNOWN": 0}
    for event in events:
        direction = str(event.get("direction", "UNKNOWN")).upper()
        result[direction if direction in result else "UNKNOWN"] += 1
    return result


@dataclass(frozen=True, slots=True)
class PoolLiquidityContext:
    pool_id: str
    liquidity_before: int
    liquidity_after: int
    context_id: str


def bind_pool_liquidity(pool_id: str, before: int, after: int) -> PoolLiquidityContext:
    if not pool_id.strip() or min(before, after) < 0:
        raise ValueError("invalid liquidity context")
    identity = {"after": after, "before": before, "pool_id": pool_id.strip(),
                "schema_version": "pool_liquidity_context.v1"}
    return PoolLiquidityContext(pool_id, before, after, deterministic_id("pool_liquidity_context", identity))


@dataclass(frozen=True, slots=True)
class WalletFundingProvenance:
    wallet: str
    funders: tuple[str, ...]
    provenance_id: str


def build_funding_provenance(wallet: str, funders: tuple[str, ...]) -> WalletFundingProvenance:
    if not wallet.strip() or not funders:
        raise ValueError("wallet and funders are required")
    identity = {"funders": funders, "schema_version": "wallet_funding_provenance.v1",
                "wallet": wallet.strip()}
    return WalletFundingProvenance(wallet, funders, deterministic_id("wallet_funding_provenance", identity))


def early_entry_consistency(entries: tuple[int, ...], first_slots: tuple[int, ...]) -> int:
    if not entries or len(entries) != len(first_slots):
        raise ValueError("entry samples mismatch")
    return sum(entry <= first for entry, first in zip(entries, first_slots)) * 10000 // len(entries)


@dataclass(frozen=True, slots=True)
class WashTradeConfidenceEvidence:
    wallet: str
    confidence_bps: int
    reason: str
    evidence_id: str


def build_wash_trade_confidence(wallet: str, confidence_bps: int, reason: str) -> WashTradeConfidenceEvidence:
    if not wallet.strip() or not 0 <= confidence_bps <= 10000 or not reason.strip():
        raise ValueError("invalid wash trade confidence")
    identity = {"confidence_bps": confidence_bps, "reason": reason.strip(),
                "schema_version": "wash_trade_confidence.v1", "wallet": wallet.strip()}
    return WashTradeConfidenceEvidence(wallet, confidence_bps, reason,
                                       deterministic_id("wash_trade_confidence", identity))


@dataclass(frozen=True, slots=True)
class ConsolidatedCandidateFeatures:
    wallet: str
    token: str
    buy_count: int
    sell_count: int
    early_entry_bps: int
    liquidity_delta: int
    feature_id: str


def consolidate_candidate_features(wallet: str, token: str, directions: Mapping[str, int],
                                   early_bps: int, liquidity_delta: int) -> ConsolidatedCandidateFeatures:
    identity = {"buy_count": directions.get("BUY", 0), "early_entry_bps": early_bps,
                "liquidity_delta": liquidity_delta, "schema_version": "candidate_features.v1",
                "sell_count": directions.get("SELL", 0), "token": token.strip(), "wallet": wallet.strip()}
    return ConsolidatedCandidateFeatures(wallet, token, identity["buy_count"], identity["sell_count"],
                                         early_bps, liquidity_delta,
                                         deterministic_id("candidate_features", identity))


def replay_candidate_ranking(features: tuple[ConsolidatedCandidateFeatures, ...]) -> tuple[ConsolidatedCandidateFeatures, ...]:
    return tuple(sorted(features, key=lambda item: (-item.early_entry_bps, -item.buy_count, item.wallet, item.token)))


def build_candidate_dashboard(features: tuple[ConsolidatedCandidateFeatures, ...]) -> dict[str, Any]:
    return {"schema_version": "production_candidate_dashboard.v1",
            "rows": tuple({"wallet": item.wallet, "token": item.token, "feature_id": item.feature_id}
                          for item in replay_candidate_ranking(features))}


def project_candidate_features(feature: ConsolidatedCandidateFeatures, slot: int) -> EvidencePayload:
    return EvidencePayload(source_id="production-candidate", evidence_type="candidate_features",
                           timestamp=slot, data={"features": {
                               "wallet": feature.wallet, "token": feature.token,
                               "buy_count": feature.buy_count, "sell_count": feature.sell_count,
                               "early_entry_bps": feature.early_entry_bps,
                               "liquidity_delta": feature.liquidity_delta,
                               "feature_id": feature.feature_id}},
                           metadata={"authority": "NONE", "classification": "EVIDENCE",
                                     "verification_status": "UNKNOWN"})


__all__ = ["adapt_rpc_transaction", "resolve_balance_accounts", "consolidate_directions",
           "PoolLiquidityContext", "bind_pool_liquidity", "WalletFundingProvenance",
           "build_funding_provenance", "early_entry_consistency", "WashTradeConfidenceEvidence",
           "build_wash_trade_confidence", "ConsolidatedCandidateFeatures",
           "consolidate_candidate_features", "replay_candidate_ranking",
           "build_candidate_dashboard", "project_candidate_features"]
