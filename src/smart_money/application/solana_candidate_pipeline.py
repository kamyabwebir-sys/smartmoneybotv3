from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from smart_money.application.mainnet_replay import replay_transaction_fixture
from smart_money.application.ports.evidence_ledger import EvidenceLedger


def replay_transaction_batch(paths: tuple[str, ...], ledger: EvidenceLedger) -> tuple[str, ...]:
    if not paths:
        raise ValueError("paths must not be empty")
    return tuple(replay_transaction_fixture(path, ledger) for path in paths)


def aggregate_balance_deltas(rows: tuple[Mapping[str, Any], ...]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in rows:
        owner = str(row.get("owner", "")).strip()
        mint = str(row.get("mint", "")).strip()
        if owner and mint:
            key = f"{owner}:{mint}"
            totals[key] = totals.get(key, 0) + int(row.get("delta", 0))
    return dict(sorted(totals.items()))


def extract_token_balance_deltas(result: Mapping[str, Any], wallet: str) -> tuple[dict[str, Any], ...]:
    """Extract canonical per-mint deltas for one wallet from an RPC result."""
    if not wallet.strip() or not isinstance(result, Mapping):
        raise ValueError("result and wallet are required")
    meta = result.get("meta", {})
    if not isinstance(meta, Mapping):
        return ()
    pre = {str(x.get("accountIndex")): x for x in meta.get("preTokenBalances", ()) if isinstance(x, Mapping)}
    post = {str(x.get("accountIndex")): x for x in meta.get("postTokenBalances", ()) if isinstance(x, Mapping)}
    rows: list[dict[str, Any]] = []
    for index in sorted(set(pre) | set(post)):
        before, after = pre.get(index, {}), post.get(index, {})
        owner = str(after.get("owner") or before.get("owner") or "").strip()
        if owner.lower() != wallet.strip().lower():
            continue
        mint = str(after.get("mint") or before.get("mint") or "").strip()
        if not mint:
            continue
        def amount(item: Mapping[str, Any]) -> int:
            token = item.get("uiTokenAmount", {})
            value = token.get("amount", 0) if isinstance(token, Mapping) else 0
            return int(value)
        rows.append({"owner": owner, "mint": mint, "delta": amount(after) - amount(before), "account_index": index})
    return tuple(rows)


def classify_transaction_programs(result: Mapping[str, Any]) -> tuple[str, ...]:
    """Return deterministic venue labels observed in top-level and inner instructions."""
    labels: set[str] = set()
    meta = result.get("meta", {}) if isinstance(result, Mapping) else {}
    tx = result.get("transaction", {}) if isinstance(result, Mapping) else {}
    message = tx.get("message", {}) if isinstance(tx, Mapping) else {}
    groups = [message.get("instructions", ())]
    groups.extend(item.get("instructions", ()) for item in meta.get("innerInstructions", ()) if isinstance(item, Mapping))
    for instruction_group in groups:
        for instruction in instruction_group or ():
            if not isinstance(instruction, Mapping):
                continue
            text = " ".join(str(instruction.get(key, "")) for key in ("program", "programId")).lower()
            for needle, label in (("raydium", "RAYDIUM"), ("jupiter", "JUPITER"), ("orca", "ORCA"), ("pump", "PUMP_FUN")):
                if needle in text:
                    labels.add(label)
    return tuple(sorted(labels))


SOLANA_PROGRAM_ID_REGISTRY = {
    "11111111111111111111111111111111": "SYSTEM",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "SPL_TOKEN",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL": "ASSOCIATED_TOKEN",
}


def extract_pool_route(result: Mapping[str, Any]) -> dict[str, Any]:
    """Extract explicit pool/route hints from parsed instruction accounts."""
    pools: set[str] = set()
    route: list[str] = []
    for label in classify_transaction_programs(result):
        route.append(label)
    meta = result.get("meta", {}) if isinstance(result, Mapping) else {}
    for group in meta.get("innerInstructions", ()) if isinstance(meta, Mapping) else ():
        for instruction in group.get("instructions", ()) if isinstance(group, Mapping) else ():
            info = instruction.get("parsed", {}).get("info", {}) if isinstance(instruction, Mapping) else {}
            if isinstance(info, Mapping):
                for key in ("pool", "amm", "poolId", "market", "source", "destination"):
                    value = info.get(key)
                    if isinstance(value, str) and value.strip() and key in {"pool", "amm", "poolId", "market"}:
                        pools.add(value.strip())
    return {"venues": tuple(route), "pools": tuple(sorted(pools)), "route_id": ">".join(route) if route else "UNKNOWN"}


def remove_internal_transfers(rows: tuple[Mapping[str, Any], ...], wallet: str) -> tuple[dict[str, Any], ...]:
    """Drop self transfers and zero deltas before candidate scoring."""
    normalized = wallet.strip().lower()
    return tuple(dict(row) for row in rows if int(row.get("delta", 0)) != 0 and str(row.get("source", "")).strip().lower() != normalized and str(row.get("destination", "")).strip().lower() != normalized)


def rank_wallet_token_candidates(
    candidates: tuple[Mapping[str, Any], ...], *,
    excluded_subjects: frozenset[tuple[str, str]] = frozenset(),
) -> tuple[dict[str, Any], ...]:
    def score(item: Mapping[str, Any]) -> int:
        if (str(item.get("wallet", "")), str(item.get("mint", ""))) in excluded_subjects:
            return 0
        buys = int(item.get("buy_count", 0))
        sells = int(item.get("sell_count", 0))
        venues = len(item.get("venues", ()))
        return buys * 3000 + min(sells, buys) * 1000 + venues * 250
    ranked = [dict(item, score_bps=min(10000, score(item))) for item in candidates]
    return tuple(sorted(ranked, key=lambda item: (-int(item["score_bps"]), str(item.get("wallet", "")), str(item.get("mint", "")))))


def attribute_program(program_id: str) -> str:
    normalized = program_id.strip().lower()
    return {"raydium": "RAYDIUM", "jupiter": "JUPITER", "orca": "ORCA", "pumpfun": "PUMP_FUN"}.get(normalized, "UNKNOWN")


@dataclass(frozen=True, slots=True)
class WalletBehaviorProfile:
    wallet: str
    activity_count: int
    buy_count: int
    sell_count: int
    profile_id: str


def build_wallet_profile(wallet: str, activities: tuple[Mapping[str, Any], ...]) -> WalletBehaviorProfile:
    if not wallet.strip():
        raise ValueError("wallet must be non-empty")
    buy = sum(str(item.get("direction", "")).upper() == "BUY" for item in activities)
    sell = sum(str(item.get("direction", "")).upper() == "SELL" for item in activities)
    count = len(activities)
    profile_id = f"{wallet.strip()}:{count}:{buy}:{sell}"
    return WalletBehaviorProfile(wallet.strip(), count, buy, sell, profile_id)


def rank_smart_money_profiles(profiles: tuple[WalletBehaviorProfile, ...]) -> tuple[WalletBehaviorProfile, ...]:
    return tuple(sorted(profiles, key=lambda item: (-(item.buy_count * 2 + item.activity_count), item.wallet)))


def dashboard_candidate_view(profiles: tuple[WalletBehaviorProfile, ...]) -> dict[str, Any]:
    return {"schema_version": "solana_candidate_dashboard.v1", "read_only": True, "items": tuple({"wallet": item.wallet, "activity_count": item.activity_count, "buy_count": item.buy_count, "sell_count": item.sell_count, "profile_id": item.profile_id} for item in rank_smart_money_profiles(profiles))}


def infer_direction(native_delta: int, token_delta: int) -> str:
    if token_delta > 0 and native_delta < 0:
        return "BUY"
    if token_delta < 0 and native_delta > 0:
        return "SELL"
    return "UNKNOWN"


def early_entry_bps(entry_slot: int, first_liquidity_slot: int) -> int:
    if entry_slot < 0 or first_liquidity_slot < 0:
        raise ValueError("slots must be non-negative")
    return 10000 if entry_slot <= first_liquidity_slot else 0


def join_candidate_context(profile: WalletBehaviorProfile, *, safety_status: str, funding_links: int) -> dict[str, Any]:
    if safety_status not in {"SAFE", "WARNING", "UNKNOWN", "CONFLICT"} or funding_links < 0:
        raise ValueError("invalid candidate context")
    return {"wallet": profile.wallet, "profile_id": profile.profile_id, "safety_status": safety_status, "funding_links": funding_links, "activity_count": profile.activity_count}


def aggregate_token_lifecycle(events: tuple[Mapping[str, Any], ...]) -> dict[str, dict[str, int]]:
    lifecycle: dict[str, dict[str, int]] = {}
    for event in events:
        mint = str(event.get("mint", "")).strip()
        if mint:
            state = lifecycle.setdefault(mint, {"observations": 0, "first_slot": int(event.get("slot", 0))})
            state["observations"] += 1
            state["first_slot"] = min(state["first_slot"], int(event.get("slot", state["first_slot"])))
    return dict(sorted(lifecycle.items()))


def build_candidate_confidence(*, early_entry: int, safety_ok: bool, funding_links: int) -> int:
    if not 0 <= early_entry <= 10000 or funding_links < 0:
        raise ValueError("invalid confidence inputs")
    return min(10000, (early_entry * 6 + (2500 if safety_ok else 0) + min(funding_links, 10) * 250) // 10)


def batch_wallet_capture(wallets: tuple[str, ...], capture: Any) -> dict[str, Any]:
    if not wallets or not callable(capture):
        raise ValueError("wallets and capture are required")
    return {wallet: capture(wallet) for wallet in sorted(set(wallets))}


def discover_token_mints(transactions: tuple[Mapping[str, Any], ...]) -> tuple[str, ...]:
    mints = {str(item.get("mint", "")).strip() for item in transactions}
    return tuple(sorted(mint for mint in mints if mint))


def fetch_token_safety(mint: str, provider: Any) -> Mapping[str, Any]:
    if not mint.strip() or not callable(provider):
        raise ValueError("mint and safety provider are required")
    result = provider(mint.strip())
    if not isinstance(result, Mapping):
        raise TypeError("safety provider must return a mapping")
    return dict(result)


def extract_funding_transfers(transfers: tuple[Mapping[str, Any], ...], wallet: str) -> tuple[str, ...]:
    if not wallet.strip():
        raise ValueError("wallet must be non-empty")
    return tuple(sorted({str(item.get("from", "")).strip() for item in transfers if str(item.get("to", "")).strip().lower() == wallet.strip().lower() and str(item.get("from", "")).strip()}))


def calibrate_confidence(predicted: tuple[int, ...], outcomes: tuple[bool, ...]) -> int:
    if not predicted or len(predicted) != len(outcomes):
        raise ValueError("calibration samples mismatch")
    error = sum(abs(score - (10000 if outcome else 0)) for score, outcome in zip(predicted, outcomes)) // len(predicted)
    return max(0, 10000 - error)


__all__ = ["replay_transaction_batch", "aggregate_balance_deltas", "extract_token_balance_deltas", "classify_transaction_programs", "SOLANA_PROGRAM_ID_REGISTRY", "extract_pool_route", "remove_internal_transfers", "rank_wallet_token_candidates", "attribute_program", "WalletBehaviorProfile", "build_wallet_profile", "rank_smart_money_profiles", "dashboard_candidate_view", "infer_direction", "early_entry_bps", "join_candidate_context", "aggregate_token_lifecycle", "build_candidate_confidence", "batch_wallet_capture", "discover_token_mints", "fetch_token_safety", "extract_funding_transfers", "calibrate_confidence"]
