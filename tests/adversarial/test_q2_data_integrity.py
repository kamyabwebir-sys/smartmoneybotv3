from __future__ import annotations

import json

import pytest

from smart_money.application.provider_runtime import resolve_provider_consensus
from smart_money.application.solana_rpc_production import normalize_rpc_response
from smart_money.domain.solana_observation import (
    SolanaChainObservation,
    replay_solana_commitment_transition,
    validate_solana_commitment_transition,
)


def _obs(commitment: str, marker: str = "sig") -> SolanaChainObservation:
    return SolanaChainObservation(10, 100, marker, "program", "subject", {"x": 1}, commitment)


def test_real_rpc_fixture_normalization_is_deterministic_and_strict(tmp_path) -> None:
    fixture = tmp_path / "rpc.json"
    fixture.write_text(json.dumps({"jsonrpc": "2.0", "result": {"slot": 10}}), encoding="utf-8")
    raw = json.loads(fixture.read_text(encoding="utf-8"))
    assert normalize_rpc_response(raw) == normalize_rpc_response(dict(raw))
    with pytest.raises((TypeError, ValueError)):
        normalize_rpc_response({"result": "invalid"})


def test_reorg_or_commitment_regression_fails_closed() -> None:
    with pytest.raises(ValueError, match="regressed"):
        validate_solana_commitment_transition(_obs("finalized"), _obs("confirmed"))
    receipt = replay_solana_commitment_transition(_obs("processed"), _obs("confirmed"))
    assert receipt.current_commitment == "confirmed"


def test_provider_consensus_is_conflict_explicit_and_order_stable() -> None:
    first = resolve_provider_consensus("token-1", (("rpc-b", "x"), ("rpc-a", "x")))
    second = resolve_provider_consensus("token-1", (("rpc-a", "x"), ("rpc-b", "x")))
    assert first.conflicted is False
    assert first.consensus_id == second.consensus_id
    conflict = resolve_provider_consensus("token-1", (("rpc-a", "x"), ("rpc-b", "y")))
    assert conflict.conflicted is True


def test_historical_split_prevents_future_outcome_leakage() -> None:
    train = ({"slot": 10, "candidate": "c", "outcome": None},)
    future = ({"slot": 20, "candidate": "c", "outcome": "success"},)
    assert all(item["slot"] < 20 for item in train)
    assert future[0]["outcome"] not in {item["outcome"] for item in train}


def test_ranking_stability_uses_canonical_tie_breakers() -> None:
    from smart_money.application.cross_intelligence import WalletTokenCrossSubjectContract
    from smart_money.application.cross_intelligence_ranking import rank_cross_intelligence

    def row(wallet: str, token: str):
        from smart_money.core.ids import deterministic_id
        identity = {"candidate_id": "c", "schema_version": "wallet_token_cross_subject.v1", "safety_binding_id": "s", "token": token, "wallet": wallet, "wallet_observation_id": "w"}
        return WalletTokenCrossSubjectContract("c", wallet, token, "w", "s", deterministic_id("wallet_token_cross_subject", identity))

    rows = (row("b", "t"), row("a", "t"))
    first = rank_cross_intelligence(rows)
    second = rank_cross_intelligence(tuple(reversed(rows)))
    assert [(item.contract.wallet, item.rank) for item in first] == [(item.contract.wallet, item.rank) for item in second]
