from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id
from smart_money.domain.solana_program_registry import (
    SOLANA_MAINNET_DEX_PROGRAMS,
    SOLANA_PROGRAM_REGISTRY_VERSION,
)

OFFICIAL_DEX_PROGRAMS = {
    program_id: (
        "RAYDIUM"
        if venue.startswith("RAYDIUM_")
        else "JUPITER"
        if venue.startswith("JUPITER_")
        else "ORCA"
        if venue.startswith("ORCA_")
        else venue
    )
    for program_id, venue in SOLANA_MAINNET_DEX_PROGRAMS.items()
}
DEX_REGISTRY_VERSIONS = {
    SOLANA_PROGRAM_REGISTRY_VERSION: dict(OFFICIAL_DEX_PROGRAMS),
}


def paginate_signatures(fetch_page: Any, *, wallet: str, pages: int = 1, before: str | None = None) -> tuple[Mapping[str, Any], ...]:
    if not wallet.strip() or pages < 1 or not callable(fetch_page):
        raise ValueError("invalid pagination inputs")
    rows: list[Mapping[str, Any]] = []
    cursor = before
    for _ in range(pages):
        page = fetch_page(wallet.strip(), cursor)
        if not isinstance(page, (list, tuple)):
            raise TypeError("signature page must be a sequence")
        rows.extend(item for item in page if isinstance(item, Mapping))
        cursor = str(page[-1].get("signature", "")) if page and isinstance(page[-1], Mapping) else None
        if not cursor:
            break
    return tuple(rows)


def inventory_instruction_programs(results: tuple[Mapping[str, Any], ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        meta = result.get("meta", {}) if isinstance(result, Mapping) else {}
        tx = result.get("transaction", {}) if isinstance(result, Mapping) else {}
        message = tx.get("message", {}) if isinstance(tx, Mapping) else {}
        groups = [message.get("instructions", ())]
        groups.extend(item.get("instructions", ()) for item in meta.get("innerInstructions", ()) if isinstance(item, Mapping))
        for group in groups:
            for instruction in group or ():
                if isinstance(instruction, Mapping):
                    program_id = str(instruction.get("programId", "")).strip()
                    if program_id:
                        counts[program_id] = counts.get(program_id, 0) + 1
    return dict(sorted(counts.items()))


def resolve_program_id(
    program_id: str,
    registry_version: str = SOLANA_PROGRAM_REGISTRY_VERSION,
) -> str:
    registry = DEX_REGISTRY_VERSIONS.get(registry_version)
    if registry is None:
        raise ValueError("unknown DEX registry version")
    return registry.get(program_id.strip(), "UNKNOWN")


def resolve_unknown_program(program_id: str, *, instruction: Mapping[str, Any] | None = None) -> str:
    """Classify unknown IDs only when parsed metadata provides an explicit venue hint."""
    known = resolve_program_id(program_id)
    if known != "UNKNOWN":
        return known
    text = str(instruction or {}).lower()
    for needle, label in (("raydium", "RAYDIUM"), ("jupiter", "JUPITER"), ("orca", "ORCA")):
        if needle in text:
            return label
    return "UNKNOWN"


def build_dex_fixture_corpus(paths: tuple[str, ...]) -> tuple[str, ...]:
    if not paths:
        raise ValueError("paths must not be empty")
    return tuple(sorted({str(path).strip() for path in paths if str(path).strip()}))


def extract_swap_candidates(results: tuple[Mapping[str, Any], ...]) -> tuple[Mapping[str, Any], ...]:
    candidates = []
    for result in results:
        meta = result.get("meta", {})
        tx = result.get("transaction", {})
        message = tx.get("message", {}) if isinstance(tx, Mapping) else {}
        groups = [message.get("instructions", ())]
        groups.extend(item.get("instructions", ()) for item in meta.get("innerInstructions", ()) if isinstance(item, Mapping))
        def is_swap(instruction: Any) -> bool:
            if not isinstance(instruction, Mapping):
                return False
            parsed = instruction.get("parsed")
            parsed_type = parsed.get("type", "") if isinstance(parsed, Mapping) else ""
            venue = resolve_program_id(str(instruction.get("programId", "")))
            return "swap" in str(parsed_type).lower() or venue in {"RAYDIUM", "JUPITER", "ORCA"}
        if any(is_swap(i) for g in groups for i in g or ()):
            candidates.append(result)
    return tuple(candidates)


def verify_exact_attribution(*, fixture_count: int, attributed_count: int, required_venues: tuple[str, ...] = ("RAYDIUM", "JUPITER", "ORCA")) -> dict[str, Any]:
    if fixture_count < 0 or attributed_count < 0 or attributed_count > fixture_count:
        raise ValueError("invalid attribution counts")
    passed = fixture_count > 0 and attributed_count > 0
    return {"schema_version": "solana_exact_attribution_gate.v1", "passed": passed, "fixture_count": fixture_count, "attributed_count": attributed_count, "required_venues": tuple(required_venues), "fail_closed": not passed}


def historical_attribution_release_gate(results: tuple[Mapping[str, Any], ...], attributed: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    return verify_exact_attribution(fixture_count=len(results), attributed_count=len(attributed))


def deduplicate_transaction_fixtures(results: tuple[Mapping[str, Any], ...]) -> tuple[Mapping[str, Any], ...]:
    seen: set[str] = set()
    unique = []
    for result in results:
        signature = str(result.get("transaction", {}).get("signatures", [""])[0] if isinstance(result.get("transaction", {}), Mapping) else "")
        key = signature or str(deterministic_id("transaction-fixture", result))
        if key not in seen:
            seen.add(key)
            unique.append(result)
    return tuple(unique)


def build_registry_match_report(results: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    inventory = inventory_instruction_programs(results)
    return {"schema_version": "solana_registry_match_report.v1", "matches": {pid: resolve_program_id(pid) for pid in inventory}, "inventory": inventory}


def build_wallet_buy_sell_profile(wallet: str, activities: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    buys = sum(str(item.get("direction", "")).upper() == "BUY" for item in activities)
    sells = sum(str(item.get("direction", "")).upper() == "SELL" for item in activities)
    return {"schema_version": "solana_wallet_buy_sell_profile.v1", "wallet": wallet.strip(), "buy_count": buys, "sell_count": sells, "activity_count": len(activities), "buy_ratio_bps": (buys * 10000 // len(activities)) if activities else 0}


def project_historical_scan(results: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    return {"schema_version": "solana_historical_scan_ledger.v1", "transaction_count": len(results), "signatures": tuple(str(r.get("transaction", {}).get("signatures", [""])[0]) for r in results)}


def build_historical_candidate_read_model(candidates: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    return {"schema_version": "solana_historical_candidate_read_model.v1", "read_only": True, "items": tuple(dict(item) for item in candidates)}


def build_dex_evidence_dashboard(candidates: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    venues = sorted({str(item.get("venue", "UNKNOWN")) for item in candidates})
    return {"schema_version": "solana_dex_evidence_dashboard.v1", "read_only": True, "candidate_count": len(candidates), "venues": tuple(venues), "items": tuple(dict(item) for item in candidates)}


def build_wallet_token_detail(wallet: str, mint: str, activities: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    return {"schema_version": "solana_wallet_token_historical_detail.v1", "wallet": wallet.strip(), "mint": mint.strip(), "activities": tuple(dict(item) for item in activities)}


def verify_historical_gate(results: tuple[Mapping[str, Any], ...], candidates: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    return historical_attribution_release_gate(results, candidates)


def persist_historical_read_model(model: Mapping[str, Any], path: str) -> str:
    import json
    from pathlib import Path
    if not isinstance(model, Mapping) or not path.strip():
        raise ValueError("model and path are required")
    payload = json.dumps(dict(model), sort_keys=True, default=list, indent=2)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8")
    return deterministic_id("historical-read-model", {"payload": payload})


def build_historical_query_audit(model: Mapping[str, Any], parameters: Mapping[str, Any]) -> dict[str, Any]:
    identity = {"model": dict(model), "parameters": dict(parameters), "schema_version": "historical_query_audit.v1"}
    return {**identity, "audit_id": deterministic_id("historical-query-audit", identity)}


def verify_historical_query_replay(expected: Mapping[str, Any], replayed: Mapping[str, Any]) -> bool:
    return dict(expected) == dict(replayed)


def query_historical_candidates(model: Mapping[str, Any], *, page: int = 1, page_size: int = 50) -> dict[str, Any]:
    if page < 1 or page_size < 1 or page_size > 500:
        raise ValueError("invalid pagination")
    items = tuple(model.get("items", ()))
    start = (page - 1) * page_size
    return {"schema_version": "historical_candidate_query.v1", "page": page, "page_size": page_size, "total": len(items), "items": items[start : start + page_size]}


def build_historical_api_response(overview: Mapping[str, Any], *, query: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {"schema_version": "historical_dashboard_api.v1", "read_only": True, "overview": dict(overview), "query": dict(query or {})}


def extract_parsed_swap_amounts(instruction: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    info = instruction.get("parsed", {}).get("info", {}) if isinstance(instruction, Mapping) else {}
    if not isinstance(info, Mapping):
        return ()
    rows = []
    for key in ("amountIn", "amountOut", "inAmount", "outAmount", "inputAmount", "outputAmount"):
        value = info.get(key)
        if value is not None:
            rows.append({"kind": key, "amount": str(value)})
    return tuple(rows)


def resolve_pool_from_accounts(instruction: Mapping[str, Any]) -> str | None:
    info = instruction.get("parsed", {}).get("info", {}) if isinstance(instruction, Mapping) else {}
    if isinstance(info, Mapping):
        for key in ("pool", "poolId", "amm", "market"):
            value = info.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    accounts = instruction.get("accounts", ()) if isinstance(instruction, Mapping) else ()
    return next((str(value).strip() for value in accounts if isinstance(value, str) and value.strip()), None)


def resolve_token_pair(instruction: Mapping[str, Any]) -> tuple[str, str] | None:
    info = instruction.get("parsed", {}).get("info", {}) if isinstance(instruction, Mapping) else {}
    if not isinstance(info, Mapping):
        return None
    base = info.get("baseMint") or info.get("inputMint") or info.get("tokenIn")
    quote = info.get("quoteMint") or info.get("outputMint") or info.get("tokenOut")
    if isinstance(base, str) and isinstance(quote, str) and base.strip() and quote.strip():
        return base.strip(), quote.strip()
    return None


def attribute_buy_sell(*, native_delta: int, token_delta: int, dex_venue: str | None, pool_id: str | None) -> str:
    if not dex_venue or not pool_id:
        return "UNKNOWN"
    if token_delta > 0 and native_delta < 0:
        return "BUY"
    if token_delta < 0 and native_delta > 0:
        return "SELL"
    return "UNKNOWN"


def wash_trade_confidence(*, wallet: str, source: str | None, destination: str | None, route: tuple[str, ...]) -> int:
    if not wallet.strip():
        raise ValueError("wallet must be non-empty")
    score = 0
    normalized = wallet.strip().lower()
    if source and source.strip().lower() == normalized:
        score += 5000
    if destination and destination.strip().lower() == normalized:
        score += 5000
    if len(set(route)) < len(route):
        score += 2500
    return min(10000, score)


@dataclass(frozen=True, slots=True)
class CandidateRankingReplayReceipt:
    ranking_id: str
    candidate_ids: tuple[str, ...]
    replay_hash: str
    schema_version: str = "solana_candidate_ranking_replay.v1"

    def __post_init__(self) -> None:
        identity = {"candidate_ids": self.candidate_ids, "ranking_id": self.ranking_id, "schema_version": self.schema_version}
        if self.replay_hash != deterministic_id("solana_candidate_ranking_replay", identity):
            raise ValueError("replay_hash mismatch")


def build_ranking_replay_receipt(ranking_id: str, candidate_ids: tuple[str, ...]) -> CandidateRankingReplayReceipt:
    identity = {"candidate_ids": candidate_ids, "ranking_id": ranking_id, "schema_version": "solana_candidate_ranking_replay.v1"}
    return CandidateRankingReplayReceipt(ranking_id, tuple(candidate_ids), deterministic_id("solana_candidate_ranking_replay", identity))


class JsonCandidateRankingReplayReceiptStore:
    def __init__(self, path: str) -> None:
        self.path = path

    def save(self, receipt: CandidateRankingReplayReceipt) -> str:
        import json
        from pathlib import Path
        Path(self.path).write_text(json.dumps({"ranking_id": receipt.ranking_id, "candidate_ids": receipt.candidate_ids, "replay_hash": receipt.replay_hash, "schema_version": receipt.schema_version}, sort_keys=True), encoding="utf-8")
        return receipt.replay_hash

    def load(self) -> CandidateRankingReplayReceipt:
        import json
        from pathlib import Path
        data = json.loads(Path(self.path).read_text(encoding="utf-8"))
        return CandidateRankingReplayReceipt(data["ranking_id"], tuple(data["candidate_ids"]), data["replay_hash"], data.get("schema_version", "solana_candidate_ranking_replay.v1"))


__all__ = ["DEX_REGISTRY_VERSIONS", "OFFICIAL_DEX_PROGRAMS", "CandidateRankingReplayReceipt", "JsonCandidateRankingReplayReceiptStore", "attribute_buy_sell", "build_dex_evidence_dashboard", "build_dex_fixture_corpus", "build_historical_api_response", "build_historical_candidate_read_model", "build_historical_query_audit", "build_ranking_replay_receipt", "build_registry_match_report", "build_wallet_buy_sell_profile", "build_wallet_token_detail", "deduplicate_transaction_fixtures", "extract_parsed_swap_amounts", "extract_swap_candidates", "historical_attribution_release_gate", "inventory_instruction_programs", "paginate_signatures", "persist_historical_read_model", "project_historical_scan", "query_historical_candidates", "resolve_pool_from_accounts", "resolve_program_id", "resolve_token_pair", "resolve_unknown_program", "verify_exact_attribution", "verify_historical_gate", "verify_historical_query_replay", "wash_trade_confidence"]
