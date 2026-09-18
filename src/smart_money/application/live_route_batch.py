"""Single-fetch live batch with fail-closed directional candidate exclusion."""
from smart_money.application.directional_purchase import (
    evaluate_directional_purchase,
    rank_purchase_evaluations,
)


def run_route_checked_batch(fetch_signatures, fetch_transaction, wallet: str, limit: int = 20) -> dict:
    if type(limit) is not int or not 1 <= limit <= 1000 or not isinstance(wallet, str) or not wallet.strip():
        raise ValueError("invalid batch inputs")
    page = fetch_signatures(wallet, limit, None)
    if not isinstance(page, dict) or page.get("error") or not isinstance(page.get("result"), list):
        raise ValueError("invalid signature page")
    reports, failures, seen, swaps, evaluations = [], [], set(), [], []
    for row in page["result"][:limit]:
        signature = row.get("signature") if isinstance(row, dict) else None
        if not isinstance(signature, str) or not signature:
            failures.append({"signature": None, "reason": "invalid_signature"})
            continue
        if signature in seen:
            continue
        seen.add(signature)
        try:
            response = fetch_transaction(signature)
            if not isinstance(response, dict) or response.get("error"):
                raise ValueError("invalid transaction response")
            raw = response.get("result")
            evaluation = evaluate_directional_purchase(raw, wallet)
            report = evaluation["route"]
            if report["signature"] != signature:
                raise ValueError("signature mismatch")
            swaps.append(dict(signature=signature, **evaluation["swaps"]))
            reports.append(report)
            evaluations.append(evaluation)
        except (ValueError, KeyError, TypeError, IndexError, AttributeError, OSError, RuntimeError):
            failures.append({"signature": signature, "reason": "unverified_transaction"})
    ranking = rank_purchase_evaluations(evaluations)
    return {"schema_version": "route_checked_live_batch.v1", "read_only": True, "wallet": wallet,
            "signature_count": len(seen), "transaction_count": len(reports),
            "candidate_count": sum(bool(r["ranking_eligible"]) for r in ranking),
            "ranking": ranking, "route_reports": reports, "swap_legs": swaps,
            "purchase_evaluations": [e["purchase"] for e in evaluations],
            "failures": failures, "replayable": False,
            "gate": {"passed": False, "reason": "production_quality_and_human_review_not_verified"}}
