"""Offline, hash-pinned S12 fixture replay. No credentials or live RPC at read time."""
import hashlib
import json
from pathlib import Path

from smart_money.application.directional_purchase import (
    evaluate_directional_purchase,
    rank_purchase_evaluations,
)
from smart_money.application.pool_state_observation import observe_pool_state
from smart_money.application.verified_swap_legs import verify_swap_legs
from smart_money.application.wallet_route_evidence import (
    project_wallet_route,
    rank_directional_evidence,
)

FIXTURE_HASH = "fa6d50cfd32803a4c3c457baa8aa8d9ce0bbfb7233e8336844ab6752c8ad4695"
SIGNATURE = "25kP9o4k4VkpQmHnrXmqBW6HvfbBQ4Rkmb2YN325r98Nah8kbDN7oT6FFpFsbP17xhrYzfkXEwxNYg1Tbc8L49cq"
WALLET = "j1opmdubY84LUeidrPCsSGskTCYmeJVzds1UWm6nngb"
EVIDENCE_ID = "wallet_route_evidence_0b59ab0994f9c4468f0470944b229af5"
POOL_HASH = "c801239310dc53ee8106007d7fc3c1ea56a95549ad2838823a524b1b693e6a92"
PURCHASE_HASH = "de43f8e327b8bdaa70b9cc69cb25c096b3e50abc6e01f0138d643145aba48782"
PURCHASE_WALLET = "2FRFWM24vDbdCfs7k6at3dqtNKDVHghdZ1d6zmw5w2S2"
PURCHASE_ID = "observed_directional_purchase_a606d87b7e0c5157266f13770a5ac247"


def replay_route_fixture(path: Path) -> dict:
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != FIXTURE_HASH:
        raise ValueError("fixture hash mismatch")
    payload = json.loads(content)
    if payload.get("error") or not isinstance(payload.get("result"), dict):
        raise ValueError("invalid RPC result")
    report = project_wallet_route(payload["result"], WALLET)
    if report["signature"] != SIGNATURE or report["evidence_id"] != EVIDENCE_ID:
        raise ValueError("fixture replay mismatch")
    swaps = verify_swap_legs(payload["result"], report)
    pool_content = path.with_name("s12-pool-observation.json").read_bytes()
    if hashlib.sha256(pool_content).hexdigest() != POOL_HASH:
        raise ValueError("pool observation hash mismatch")
    snapshot = json.loads(pool_content)
    swaps["pool_observations"] = [observe_pool_state(snapshot, leg, payload["result"]["slot"]) for leg in swaps["legs"]]
    return {"read_only": True, "fixture_sha256": FIXTURE_HASH, "replay_verified": True,
            "report": report, "ranking": rank_directional_evidence([report]),
            "swap_verification": swaps,
            "eligible_count": 0, "scope": "single_transaction_not_wallet_profitability"}


def replay_purchase_fixture(path: Path) -> dict:
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != PURCHASE_HASH:
        raise ValueError("purchase fixture hash mismatch")
    payload = json.loads(content)
    if payload.get("error") or not isinstance(payload.get("result"), dict):
        raise ValueError("invalid purchase RPC result")
    evaluation = evaluate_directional_purchase(payload["result"], PURCHASE_WALLET)
    if evaluation["purchase"]["evidence_id"] != PURCHASE_ID or not evaluation["purchase"]["accepted"]:
        raise ValueError("purchase replay mismatch")
    ranking = rank_purchase_evaluations([evaluation])
    return {"read_only": True, "fixture_sha256": PURCHASE_HASH, "replay_verified": True,
            "report": evaluation["route"], "ranking": ranking,
            "purchase": evaluation["purchase"], "swap_verification": evaluation["swaps"],
            "eligible_count": sum(bool(row["ranking_eligible"]) for row in ranking),
            "scope": "observed_purchase_not_smart_money_or_investment_advice"}
