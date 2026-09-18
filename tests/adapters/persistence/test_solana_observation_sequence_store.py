import pytest

from smart_money.adapters.persistence.solana_observation_sequence_store import (
    JsonSolanaObservationSequenceStore,
)
from smart_money.domain.solana_observation import (
    SolanaChainObservation,
    replay_solana_observation_order,
)


def _receipt():
    values = (
        SolanaChainObservation(1, 10, "a", "program", "wallet"),
        SolanaChainObservation(2, 20, "b", "program", "wallet"),
    )
    return replay_solana_observation_order(values)


def test_sequence_store_round_trips_and_is_idempotent(tmp_path):
    path = tmp_path / "sequence.json"
    receipt = _receipt()
    first = JsonSolanaObservationSequenceStore(path)
    assert first.append(receipt) == receipt.sequence_id
    assert first.append(receipt) == receipt.sequence_id
    second = JsonSolanaObservationSequenceStore(path)
    assert second.get(receipt.sequence_id) == receipt
    assert second.receipt_count == 1
    assert second.content_hash == first.content_hash


def test_sequence_store_rejects_wrong_receipt(tmp_path):
    store = JsonSolanaObservationSequenceStore(tmp_path / "sequence.json")
    with pytest.raises(TypeError, match="SolanaOrderingReplayReceipt"):
        store.append(object())  # type: ignore[arg-type]


def test_sequence_store_replay_verifies_persisted_sequence(tmp_path):
    values = (
        SolanaChainObservation(1, 10, "a", "program", "wallet"),
        SolanaChainObservation(2, 20, "b", "program", "wallet"),
    )
    receipt = replay_solana_observation_order(values)
    store = JsonSolanaObservationSequenceStore(tmp_path / "sequence.json")
    store.append(receipt)
    assert store.replay(values) == receipt


def test_sequence_store_replay_fails_when_sequence_is_missing(tmp_path):
    store = JsonSolanaObservationSequenceStore(tmp_path / "sequence.json")
    values = (SolanaChainObservation(1, 10, "a", "program", "wallet"),)
    with pytest.raises(ValueError, match="missing"):
        store.replay(values)
