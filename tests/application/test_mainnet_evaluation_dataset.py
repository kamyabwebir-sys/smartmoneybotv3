import pytest

from smart_money.application.mainnet_evaluation_dataset import (
    build_mainnet_evaluation_dataset,
)


def discovery(candidate="c1", observed=100):
    return {"candidate_id": candidate, "observed_at_epoch": observed, "chain": "solana:mainnet-beta",
            "predicted": True, "safety_passed": True, "funding_verified": True,
            "route": "raydium_cpmm", "source_evidence_hash": "sha256:abc"}


def outcome(candidate="c1", observed=200):
    return {"candidate_id": candidate, "observed_at_epoch": observed, "outcome": "VALIDATED"}


def test_builds_time_separated_mainnet_evaluation_dataset():
    result = build_mainnet_evaluation_dataset([discovery()], [outcome()], dataset_id="mainnet-1", horizon="24h")
    assert result["split"] == "evaluation"
    assert result["provenance"]["training_overlap_count"] == 0
    assert result["items"][0]["outcome_observed_at_epoch"] > result["items"][0]["discovered_at_epoch"]


def test_rejects_leakage_training_overlap_and_wrong_chain():
    with pytest.raises(ValueError, match="strictly after"):
        build_mainnet_evaluation_dataset([discovery()], [outcome(observed=99)], dataset_id="d", horizon="24h")
    with pytest.raises(ValueError, match="training"):
        build_mainnet_evaluation_dataset([discovery()], [outcome()], dataset_id="d", horizon="24h", training_candidate_ids=frozenset({"c1"}))
    bad = discovery()
    bad["chain"] = "bsc:mainnet"
    with pytest.raises(ValueError, match="mainnet-beta"):
        build_mainnet_evaluation_dataset([bad], [outcome()], dataset_id="d", horizon="24h")
