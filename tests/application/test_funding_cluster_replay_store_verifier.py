from smart_money.adapters.persistence.funding_cluster_replay_store import JsonFundingClusterReplayStore
from smart_money.application.funding_cluster_replay import FundingClusterReplayReceipt
from smart_money.application.funding_cluster_replay_store_verifier import verify_funding_cluster_replay_store
from smart_money.core.ids import deterministic_id


def test_funding_cluster_replay_store_verifier_matches_receipt(tmp_path) -> None:
    identity = {
        "cluster_id": "cluster-1",
        "matches": True,
        "schema_version": "funding_cluster_replay.v1",
    }
    expected = FundingClusterReplayReceipt(
        **identity,
        replay_id=deterministic_id("funding_cluster_replay", identity),
    )
    store = JsonFundingClusterReplayStore(tmp_path / "replay.json")
    store.append(expected)
    verification = verify_funding_cluster_replay_store(store, expected)
    assert verification.matches is True
    assert verification.replay_id == expected.replay_id
    assert verification.verification_id
