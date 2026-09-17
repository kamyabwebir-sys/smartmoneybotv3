"""Behavior contract tests for live discovery slice — S11 attribution join."""

from __future__ import annotations

from typing import Any

from smart_money.application.live_discovery_slice import (
    build_attribution_evidence,
    build_final_live_gate,
    build_human_review_record,
    complete_buy_sell_evidence,
    enrich_session_with_attribution,
    extract_native_sol_delta,
    live_production_gate,
)


RAYDIUM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
JUPITER = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
WALLET = "9HCTuTPEiQvkUtLmTZvK6uch4E3pDynwJTbNw6jLhp9z"
MINT = "1Lxt6zCQ7jzkawfSYdKcru3NWVizJwXup5Sz3fMpump"
POOL = "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2"


def _tx(*, native_pre: int, native_post: int, token_pre: str, token_post: str, owner: str = WALLET) -> dict[str, Any]:
    return {
        "transaction": {
            "signatures": ["SIG1"],
            "message": {
                "accountKeys": [{"pubkey": owner}, {"pubkey": "other"}],
                "instructions": [{"programId": RAYDIUM, "accounts": [POOL]}],
            },
        },
        "meta": {
            "preBalances": [native_pre, 1000],
            "postBalances": [native_post, 1000],
            "preTokenBalances": [
                {"accountIndex": 0, "mint": MINT, "owner": owner, "uiTokenAmount": {"amount": token_pre}},
            ],
            "postTokenBalances": [
                {"accountIndex": 0, "mint": MINT, "owner": owner, "uiTokenAmount": {"amount": token_post}},
            ],
        },
    }


class TestExtractNativeSolDelta:
    def test_buy_reduces_native(self) -> None:
        result = _tx(native_pre=1_000_000, native_post=900_000, token_pre="0", token_post="100")
        assert extract_native_sol_delta(result, WALLET) == -100_000

    def test_sell_increases_native(self) -> None:
        result = _tx(native_pre=900_000, native_post=1_000_000, token_pre="100", token_post="0")
        assert extract_native_sol_delta(result, WALLET) == 100_000

    def test_missing_wallet_returns_zero(self) -> None:
        result = _tx(native_pre=100, native_post=200, token_pre="0", token_post="1", owner="SomeoneElse")
        assert extract_native_sol_delta(result, WALLET) == 0


class TestBuildAttributionEvidence:
    def test_buy_is_attributed_with_real_deltas(self) -> None:
        result = _tx(native_pre=1_000_000, native_post=900_000, token_pre="0", token_post="100")
        rows = build_attribution_evidence(result, WALLET)
        assert len(rows) == 1
        row = rows[0]
        assert row["direction"] == "BUY"
        assert row["verified"] is True
        assert row["native_delta"] == -100_000
        assert row["delta"] == 100
        assert row["venue"] == "RAYDIUM"
        assert row["pool_id"] == POOL

    def test_sell_is_attributed(self) -> None:
        result = _tx(native_pre=900_000, native_post=1_000_000, token_pre="100", token_post="0")
        rows = build_attribution_evidence(result, WALLET)
        assert rows[0]["direction"] == "SELL"
        assert rows[0]["verified"] is True

    def test_no_dex_venue_stays_unknown(self) -> None:
        result = _tx(native_pre=1_000_000, native_post=900_000, token_pre="0", token_post="100")
        result["transaction"]["message"]["instructions"] = [
            {"programId": "11111111111111111111111111111111", "accounts": [POOL]}
        ]
        rows = build_attribution_evidence(result, WALLET)
        assert rows[0]["direction"] == "UNKNOWN"
        assert rows[0]["verified"] is False


class TestCompleteBuySellEvidence:
    def test_direction_logic(self) -> None:
        assert complete_buy_sell_evidence(_tx(native_pre=1, native_post=0, token_pre="0", token_post="1"), WALLET, 10, POOL)["direction"] == "BUY"
        assert complete_buy_sell_evidence(_tx(native_pre=0, native_post=1, token_pre="1", token_post="0"), WALLET, -10, POOL)["direction"] == "SELL"
        assert complete_buy_sell_evidence(_tx(native_pre=1, native_post=0, token_pre="0", token_post="1"), WALLET, 10, None)["direction"] == "UNKNOWN"

    def test_no_pool_no_attribution(self) -> None:
        row = complete_buy_sell_evidence(_tx(native_pre=1, native_post=0, token_pre="0", token_post="1"), WALLET, 10, None)
        assert row["verified"] is False


class TestEnrichSessionWithAttribution:
    def test_attaches_summary_and_evidence(self) -> None:
        results = (_tx(native_pre=1_000_000, native_post=900_000, token_pre="0", token_post="100"),)
        session = {
            "wallet": WALLET,
            "transaction_count": 1,
            "candidate_count": 1,
            "program_inventory": {RAYDIUM: 1},
        }
        enriched = enrich_session_with_attribution(session, results, WALLET)
        assert enriched["attribution"]["schema_version"] == "live_attribution_summary.v1"
        assert enriched["attribution"]["evidence_count"] == 1
        assert enriched["attribution"]["verified_count"] == 1
        assert enriched["attribution"]["attributed_signatures"] == ("SIG1",)
        assert len(enriched["buy_sell_evidence"]) == 1
        assert enriched["buy_sell_evidence"][0]["direction"] == "BUY"
        # original keys preserved
        assert enriched["transaction_count"] == 1

    def test_no_candidates_yields_zero(self) -> None:
        plain = {
            "transaction": {"signatures": ["SIGX"], "message": {"accountKeys": [], "instructions": []}},
            "meta": {"preBalances": [0], "postBalances": [0], "preTokenBalances": [], "postTokenBalances": []},
        }
        session = {"wallet": WALLET, "transaction_count": 1, "candidate_count": 0}
        enriched = enrich_session_with_attribution(session, (plain,), WALLET)
        assert enriched["attribution"]["evidence_count"] == 0
        assert enriched["attribution"]["verified_count"] == 0


class TestGates:
    def test_production_gate_fail_closed(self) -> None:
        gate = live_production_gate({"transaction_count": 10, "candidate_count": 0})
        assert gate["passed"] is False
        assert gate["fail_closed"] is True

    def test_production_gate_passes(self) -> None:
        gate = live_production_gate({"transaction_count": 10, "candidate_count": 2})
        assert gate["passed"] is True

    def test_final_gate_requires_human_approval(self) -> None:
        evidence = ({"verified": True},)
        assert build_final_live_gate({"transaction_count": 5}, evidence, human_approved=False)["passed"] is False
        assert build_final_live_gate({"transaction_count": 5}, evidence, human_approved=True)["passed"] is True

    def test_human_review_record_deterministic(self) -> None:
        a = build_human_review_record("cand-1", True, "reviewer")
        b = build_human_review_record("cand-1", True, "reviewer")
        assert a["review_id"] == b["review_id"]
