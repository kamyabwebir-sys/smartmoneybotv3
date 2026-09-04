from pathlib import Path

import pytest

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_store import (
    JsonSolanaCursorSequenceCheckpointStore,
)
from smart_money.domain.solana_observation import (
    SolanaCursorSequenceCheckpoint,
    SolanaSlotCursor,
    replay_solana_observation_order,
)
from tests.domain.test_solana_observation import _observation


def _checkpoint() -> SolanaCursorSequenceCheckpoint:
    observations = (
        _observation(slot=1, observed_at=10, transaction_signature="a"),
        _observation(slot=2, observed_at=11, transaction_signature="b"),
    )
    sequence = replay_solana_observation_order(observations)
    return SolanaCursorSequenceCheckpoint.from_sequence(
        sequence, SolanaSlotCursor.from_observation(observations[-1])
    )


def test_checkpoint_store_round_trip_and_idempotent_save(tmp_path: Path):
    path = tmp_path / "checkpoint.json"
    checkpoint = _checkpoint()
    store = JsonSolanaCursorSequenceCheckpointStore(path)
    assert store.save(checkpoint) == checkpoint.checkpoint_id
    assert store.save(checkpoint) == checkpoint.checkpoint_id
    restored = JsonSolanaCursorSequenceCheckpointStore(path)
    assert restored.load() == checkpoint
    assert restored.checkpoint_id == checkpoint.checkpoint_id


def test_checkpoint_store_rejects_identity_collision(tmp_path: Path):
    store = JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json")
    checkpoint = _checkpoint()
    store.save(checkpoint)
    forged = SolanaCursorSequenceCheckpoint(
        cursor=checkpoint.cursor,
        sequence_id=checkpoint.sequence_id,
        observation_count=checkpoint.observation_count,
        last_observation_id=checkpoint.last_observation_id,
        last_ordering_key=checkpoint.last_ordering_key,
        checkpoint_id=checkpoint.checkpoint_id,
    )
    assert store.save(forged) == checkpoint.checkpoint_id


def test_checkpoint_store_rejects_non_checkpoint():
    with pytest.raises(TypeError, match="checkpoint"):
        JsonSolanaCursorSequenceCheckpointStore.__dict__["save"](  # type: ignore[misc]
            object(), object()
        )


def test_checkpoint_store_replay_verifies_persisted_checkpoint(tmp_path: Path):
    observations = (
        _observation(slot=1, observed_at=10, transaction_signature="a"),
        _observation(slot=2, observed_at=11, transaction_signature="b"),
    )
    sequence = replay_solana_observation_order(observations)
    cursor = SolanaSlotCursor.from_observation(observations[-1])
    checkpoint = SolanaCursorSequenceCheckpoint.from_sequence(sequence, cursor)
    store = JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json")
    store.save(checkpoint)
    receipt = store.replay(sequence, cursor)
    assert receipt.matches is True
    assert receipt.stored_checkpoint_id == checkpoint.checkpoint_id
    assert receipt.replay_id == store.replay(sequence, cursor).replay_id


def test_checkpoint_store_replay_fails_closed_on_mismatch(tmp_path: Path):
    observations = (
        _observation(slot=1, observed_at=10, transaction_signature="a"),
        _observation(slot=2, observed_at=11, transaction_signature="b"),
    )
    sequence = replay_solana_observation_order(observations)
    store = JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json")
    store.save(
        SolanaCursorSequenceCheckpoint.from_sequence(
            sequence, SolanaSlotCursor.from_observation(observations[-1])
        )
    )
    with pytest.raises(ValueError, match="does not match"):
        store.replay(
            sequence,
            SolanaSlotCursor.from_observation(
                _observation(slot=3, observed_at=12, transaction_signature="c")
            ),
        )
