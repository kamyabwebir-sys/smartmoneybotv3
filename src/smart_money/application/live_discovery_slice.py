from __future__ import annotations

from typing import Any, Mapping
import json
from pathlib import Path
from smart_money.core.ids import deterministic_id

from smart_money.application.solana_dex_attribution import extract_swap_candidates, inventory_instruction_programs
from smart_money.application.solana_dex_attribution import resolve_program_id, resolve_pool_from_accounts, resolve_token_pair
from smart_money.application.solana_candidate_pipeline import extract_token_balance_deltas
from smart_money.application.solana_dex_attribution import attribute_buy_sell


def run_live_read_only_session(fetch_signatures: Any, fetch_transaction: Any, wallet: str, limit: int = 20) -> dict[str, Any]:
    if not callable(fetch_signatures) or not callable(fetch_transaction) or not wallet.strip():
        raise ValueError("invalid live session inputs")
    page = fetch_signatures(wallet.strip(), limit, None)
    rows = page.get("result", ()) if isinstance(page, Mapping) else ()
    transactions = tuple(fetch_transaction(item["signature"]).get("result") for item in rows if isinstance(item, Mapping) and item.get("signature"))
    transactions = tuple(item for item in transactions if isinstance(item, Mapping))
    candidates = extract_swap_candidates(transactions)
    return {"schema_version": "solana_live_discovery_session.v1", "read_only": True, "wallet": wallet.strip(), "signature_count": len(rows), "transaction_count": len(transactions), "candidate_count": len(candidates), "program_inventory": inventory_instruction_programs(transactions), "replayable": True}


def live_production_gate(session: Mapping[str, Any], *, recovery_ok: bool = True) -> dict[str, Any]:
    processed = int(session.get("transaction_count", 0))
    candidates = int(session.get("candidate_count", 0))
    passed = processed > 0 and candidates > 0 and recovery_ok
    return {"schema_version": "solana_live_production_gate.v1", "passed": passed, "fail_closed": not passed, "processed": processed, "candidates": candidates, "recovery_ok": recovery_ok}


def persist_live_session(session: Mapping[str, Any], path: str | Path) -> str:
    target = Path(path)
    payload = json.dumps(dict(session), sort_keys=True, default=list, indent=2)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8")
    return deterministic_id("live-session", {"payload": payload})


def load_live_session(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return dict(data) if isinstance(data, Mapping) else {}


def build_live_replay_receipt(session: Mapping[str, Any]) -> dict[str, Any]:
    identity = {"session": dict(session), "schema_version": "solana_live_replay_receipt.v1"}
    return {**identity, "receipt_id": deterministic_id("solana-live-replay", identity)}


def build_live_audit_receipt(session: Mapping[str, Any], replay: Mapping[str, Any]) -> dict[str, Any]:
    identity = {"replay_id": replay.get("receipt_id"), "session_id": session.get("wallet"), "schema_version": "solana_live_audit_receipt.v1"}
    return {**identity, "audit_id": deterministic_id("solana-live-audit", identity)}


def bind_live_checkpoint(session: Mapping[str, Any], cursor: str | None) -> dict[str, Any]:
    return {"schema_version": "live_checkpoint.v1", "wallet": session.get("wallet"), "cursor": cursor, "session_id": deterministic_id("live-checkpoint", {"wallet": session.get("wallet"), "cursor": cursor})}


def project_live_candidates(session: Mapping[str, Any]) -> dict[str, Any]:
    return {"schema_version": "live_candidate_projection.v1", "read_only": True, "wallet": session.get("wallet"), "count": session.get("candidate_count", 0)}


def schedule_live_retry(attempt: int, delay_seconds: float) -> dict[str, Any]:
    if attempt < 0 or delay_seconds < 0:
        raise ValueError("invalid retry schedule")
    return {"schema_version": "live_retry_schedule.v1", "attempt": attempt, "delay_seconds": delay_seconds}


def persist_failure_receipt(error: str, path: str | Path) -> str:
    receipt = {"schema_version": "live_failure_receipt.v1", "error": error.strip()}
    return persist_live_session(receipt, path)


def build_live_ranking_read_model(items: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    return {"schema_version": "live_candidate_ranking.v1", "read_only": True, "items": tuple(sorted((dict(x) for x in items), key=lambda x: (-int(x.get("score_bps", 0)), str(x.get("wallet", "")))))}


def build_live_audit_chain(receipts: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    identity = {"receipt_ids": tuple(str(x.get("audit_id", "")) for x in receipts), "schema_version": "live_audit_chain.v1"}
    return {**identity, "head": deterministic_id("live-audit-chain", identity)}


def bind_live_fixture_directory(directory: str | Path) -> dict[str, Any]:
    path = Path(directory)
    return {"schema_version": "live_fixture_directory.v1", "path": str(path), "exists": path.is_dir(), "fixture_count": len(tuple(path.glob("*.json"))) if path.is_dir() else 0}


def build_live_dashboard_refresh(session: Mapping[str, Any]) -> dict[str, Any]:
    return {"schema_version": "live_dashboard_refresh.v1", "read_only": True, "wallet": session.get("wallet"), "candidate_count": session.get("candidate_count", 0)}


def build_live_wallet_token_detail(session: Mapping[str, Any], wallet: str, mint: str) -> dict[str, Any]:
    return {"schema_version": "live_wallet_token_detail.v1", "wallet": wallet.strip(), "mint": mint.strip(), "session_wallet": session.get("wallet")}


def build_live_dex_evidence_table(session: Mapping[str, Any]) -> dict[str, Any]:
    return {"schema_version": "live_dex_evidence_table.v1", "items": tuple(session.get("program_inventory", {}).items())}


def verify_live_recovery(before: Mapping[str, Any], after: Mapping[str, Any]) -> bool:
    return int(after.get("transaction_count", 0)) >= int(before.get("transaction_count", 0))


def extract_dex_candidate_signatures(results: tuple[Mapping[str, Any], ...]) -> tuple[str, ...]:
    out = []
    for result in results:
        tx = result.get("transaction", {})
        signature = tx.get("signatures", [""])[0] if isinstance(tx, Mapping) else ""
        programs = inventory_instruction_programs((result,))
        if any(resolve_program_id(pid) in {"RAYDIUM", "JUPITER", "ORCA"} for pid in programs):
            out.append(str(signature))
    return tuple(sorted(set(x for x in out if x)))


def decode_dex_instruction(instruction: Mapping[str, Any]) -> dict[str, Any]:
    venue = resolve_program_id(str(instruction.get("programId", "")))
    return {"venue": venue, "pool": resolve_pool_from_accounts(instruction), "token_pair": resolve_token_pair(instruction), "instruction_type": instruction.get("parsed", {}).get("type") if isinstance(instruction.get("parsed"), Mapping) else None}


def build_live_review_gate(session: Mapping[str, Any], attributed_count: int) -> dict[str, Any]:
    passed = int(session.get("candidate_count", 0)) > 0 and attributed_count > 0
    return {"schema_version": "live_smart_money_review_gate.v1", "passed": passed, "fail_closed": not passed, "candidate_count": int(session.get("candidate_count", 0)), "attributed_count": attributed_count, "human_review_required": True}


def materialize_dex_fixtures(results: tuple[Mapping[str, Any], ...], directory: str | Path) -> tuple[str, ...]:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    paths = []
    for result in results:
        signature = str(result.get("transaction", {}).get("signatures", [""])[0])
        if signature:
            path = target / f"{signature}.json"
            path.write_text(json.dumps({"result": result}, sort_keys=True, default=list), encoding="utf-8")
            paths.append(str(path))
    return tuple(paths)


def build_attribution_evidence(result: Mapping[str, Any], wallet: str) -> tuple[dict[str, Any], ...]:
    rows = extract_token_balance_deltas(result, wallet)
    evidence = []
    native_delta = extract_native_sol_delta(result, wallet)
    venues = {
        resolve_program_id(pid)
        for pid in inventory_instruction_programs((result,))
        if resolve_program_id(pid) in {"RAYDIUM", "JUPITER", "ORCA"}
    }
    pools = {resolve_pool_from_accounts(i) for i in _iter_instructions(result)}
    pool_ids = {p for p in pools if p}
    venue = sorted(venues)[0] if venues else None
    pool_id = sorted(pool_ids)[0] if pool_ids else None
    for row in rows:
        direction = attribute_buy_sell(native_delta=native_delta, token_delta=int(row["delta"]), dex_venue=venue, pool_id=pool_id)
        evidence.append({**row, "native_delta": native_delta, "venue": venue, "pool_id": pool_id, "direction": direction, "verified": direction != "UNKNOWN", "schema_version": "live_buy_sell_evidence.v2"})
    return tuple(evidence)


def _iter_instructions(result: Mapping[str, Any]):
    meta = result.get("meta", {}) if isinstance(result, Mapping) else {}
    tx = result.get("transaction", {}) if isinstance(result, Mapping) else {}
    message = tx.get("message", {}) if isinstance(tx, Mapping) else {}
    groups = [message.get("instructions", ())]
    groups.extend(item.get("instructions", ()) for item in meta.get("innerInstructions", ()) if isinstance(item, Mapping))
    for group in groups:
        for instruction in group or ():
            if isinstance(instruction, Mapping):
                yield instruction


def persist_candidate_evidence(evidence: tuple[Mapping[str, Any], ...], path: str | Path) -> str:
    return persist_live_session({"schema_version": "live_candidate_evidence.v1", "items": evidence}, path)


def extract_native_sol_delta(result: Mapping[str, Any], wallet: str) -> int:
    meta = result.get("meta", {})
    keys = result.get("transaction", {}).get("message", {}).get("accountKeys", [])
    for index, key in enumerate(keys):
        address = key.get("pubkey") if isinstance(key, Mapping) else key
        if str(address).lower() == wallet.strip().lower():
            pre, post = meta.get("preBalances", []), meta.get("postBalances", [])
            return int(post[index]) - int(pre[index])
    return 0


def validate_swap_amounts(instruction: Mapping[str, Any]) -> bool:
    info = instruction.get("parsed", {}).get("info", {}) if isinstance(instruction, Mapping) else {}
    if not isinstance(info, Mapping):
        return False
    values = [info.get(k) for k in ("amountIn", "amountOut", "inAmount", "outAmount")]
    return any(value not in (None, "", 0, "0") for value in values)


def complete_buy_sell_evidence(result: Mapping[str, Any], wallet: str, token_delta: int, pool_id: str | None) -> dict[str, Any]:
    native = extract_native_sol_delta(result, wallet)
    direction = "BUY" if token_delta > 0 and native < 0 and pool_id else "SELL" if token_delta < 0 and native > 0 and pool_id else "UNKNOWN"
    return {"wallet": wallet.strip(), "token_delta": token_delta, "native_delta": native, "pool_id": pool_id, "direction": direction, "verified": direction != "UNKNOWN", "schema_version": "live_buy_sell_evidence.v2"}


def build_wallet_profile_v3(wallet: str, evidence: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    buys = sum(x.get("direction") == "BUY" for x in evidence)
    sells = sum(x.get("direction") == "SELL" for x in evidence)
    return {"schema_version": "wallet_profile.v3", "wallet": wallet.strip(), "activity_count": len(evidence), "buy_count": buys, "sell_count": sells, "verified_count": sum(bool(x.get("verified")) for x in evidence)}


def rank_wallet_token_v3(rows: tuple[Mapping[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    ranked = [dict(x, score_bps=min(10000, int(x.get("verified_count", 0)) * 2000 + int(x.get("buy_count", 0)) * 1000)) for x in rows]
    return tuple(sorted(ranked, key=lambda x: (-int(x["score_bps"]), str(x.get("wallet", "")))))


def materialize_candidate_transactions(results: tuple[Mapping[str, Any], ...], directory: str | Path) -> tuple[str, ...]:
    return materialize_dex_fixtures(results, directory)


def join_native_token_delta(result: Mapping[str, Any], wallet: str, mint: str) -> dict[str, Any]:
    rows = extract_token_balance_deltas(result, wallet)
    token_delta = sum(int(x["delta"]) for x in rows if x.get("mint") == mint)
    return {"wallet": wallet, "mint": mint, "native_delta": extract_native_sol_delta(result, wallet), "token_delta": token_delta}


def build_outcome_window(entry_slot: int, exit_slot: int | None = None) -> dict[str, Any]:
    if entry_slot < 0 or (exit_slot is not None and exit_slot < entry_slot):
        raise ValueError("invalid outcome window")
    return {"schema_version": "live_outcome_window.v1", "entry_slot": entry_slot, "exit_slot": exit_slot, "duration_slots": None if exit_slot is None else exit_slot - entry_slot}


def build_final_live_gate(session: Mapping[str, Any], evidence: tuple[Mapping[str, Any], ...], human_approved: bool = False) -> dict[str, Any]:
    verified = sum(bool(x.get("verified")) for x in evidence)
    passed = int(session.get("transaction_count", 0)) > 0 and verified > 0 and human_approved
    return {"schema_version": "solana_final_live_release_gate.v1", "passed": passed, "fail_closed": not passed, "verified_evidence": verified, "human_approved": human_approved}


def replay_candidate_transaction(result: Mapping[str, Any], wallet: str, mint: str) -> dict[str, Any]:
    return join_native_token_delta(result, wallet, mint)


def reconcile_token_amount(expected: int, observed: int) -> dict[str, Any]:
    return {"schema_version": "token_amount_reconciliation.v1", "expected": expected, "observed": observed, "matching": expected == observed}


def build_wallet_outcome_backfill(wallet: str, outcomes: tuple[Mapping[str, Any], ...]) -> dict[str, Any]:
    return {"schema_version": "wallet_outcome_backfill.v1", "wallet": wallet.strip(), "count": len(outcomes), "outcomes": tuple(dict(x) for x in outcomes)}


def build_human_review_record(candidate_id: str, approved: bool, reviewer: str) -> dict[str, Any]:
    identity = {"candidate_id": candidate_id.strip(), "approved": approved, "reviewer": reviewer.strip(), "schema_version": "human_review_record.v1"}
    return {**identity, "review_id": deterministic_id("human-review", identity)}


def enrich_session_with_attribution(session: Mapping[str, Any], results: tuple[Mapping[str, Any], ...], wallet: str) -> dict[str, Any]:
    """Attach exact BUY/SELL evidence for every candidate transaction in a live session.

    Only candidate transactions (results containing a registered DEX program) are
    examined; evidence rows carry the real native SOL delta and per-mint token deltas
    for the wallet, and direction stays UNKNOWN whenever venue/pool evidence is missing.
    """
    candidate_results = extract_swap_candidates(results)
    evidence: list[dict[str, Any]] = []
    attributed_signatures: list[str] = []
    for result in candidate_results:
        rows = build_attribution_evidence(result, wallet)
        if not rows:
            continue
        signature = str(result.get("transaction", {}).get("signatures", [""])[0])
        evidence.extend(dict(row, signature=signature) for row in rows)
        if any(row.get("verified") for row in rows):
            attributed_signatures.append(signature)
    attributed = tuple(dict(row) for row in evidence if row.get("verified"))
    return {
        **dict(session),
        "attribution": {
            "schema_version": "live_attribution_summary.v1",
            "evidence_count": len(evidence),
            "verified_count": len(attributed),
            "attributed_signatures": tuple(sorted(set(attributed_signatures))),
        },
        "buy_sell_evidence": tuple(evidence),
    }


__all__ = ["run_live_read_only_session", "live_production_gate", "persist_live_session", "load_live_session", "build_live_replay_receipt", "build_live_audit_receipt", "bind_live_checkpoint", "project_live_candidates", "schedule_live_retry", "persist_failure_receipt", "build_live_ranking_read_model", "build_live_audit_chain", "bind_live_fixture_directory", "build_live_dashboard_refresh", "build_live_wallet_token_detail", "build_live_dex_evidence_table", "verify_live_recovery", "extract_dex_candidate_signatures", "decode_dex_instruction", "build_live_review_gate", "materialize_dex_fixtures", "build_attribution_evidence", "persist_candidate_evidence", "extract_native_sol_delta", "validate_swap_amounts", "complete_buy_sell_evidence", "build_wallet_profile_v3", "rank_wallet_token_v3", "materialize_candidate_transactions", "join_native_token_delta", "build_outcome_window", "build_final_live_gate", "replay_candidate_transaction", "reconcile_token_amount", "build_wallet_outcome_backfill", "build_human_review_record", "enrich_session_with_attribution"]
