from smart_money.adapters.persistence.funding_cluster_replay_store import JsonFundingClusterReplayStore
from smart_money.application.funding_cluster_replay import FundingClusterReplayReceipt
from smart_money.core.ids import deterministic_id


def test_funding_cluster_replay_store_is_atomic_and_idempotent(tmp_path) -> None:
    identity = {
        "cluster_id": "cluster-1",
        "matches": True,
        "schema_version": "funding_cluster_replay.v1",
    }
    receipt = FundingClusterReplayReceipt(
        **identity,
        replay_id=deterministic_id("funding_cluster_replay", identity),
    )
    path = tmp_path / "funding-cluster-replay.json"
    store = JsonFundingClusterReplayStore(path)
    assert store.append(receipt) == receipt.replay_id
    assert store.append(receipt) == receipt.replay_id
    restored = JsonFundingClusterReplayStore(path)
    assert restored.get(receipt.replay_id) == receipt
    assert restored.receipt_count == 1
