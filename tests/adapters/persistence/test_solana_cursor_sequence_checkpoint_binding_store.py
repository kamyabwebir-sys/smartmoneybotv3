from pathlib import Path

import pytest

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_binding_store import (
    JsonSolanaCursorSequenceCheckpointBindingStore,
)
from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_store import (
    JsonSolanaCursorSequenceCheckpointStore,
)
from smart_money.adapters.persistence.solana_observation_sequence_store import (
    JsonSolanaObservationSequenceStore,
)
from smart_money.adapters.persistence.solana_slot_cursor_store import JsonSolanaSlotCursorStore
from smart_money.application.solana_cursor_sequence_checkpoint_binding import (
    advance_and_checkpoint_solana_cursor,
)
from tests.domain.test_solana_observation import _observation


def test_binding_store_round_trip_and_idempotent_save(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    receipt = advance_and_checkpoint_solana_cursor(
        JsonSolanaSlotCursorStore(tmp_path / "cursor.json"),
        JsonSolanaObservationSequenceStore(tmp_path / "sequence.json"),
        JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json"),
        observations,
    )
    store = JsonSolanaCursorSequenceCheckpointBindingStore(tmp_path / "binding.json")
    assert store.save(receipt) == receipt.receipt_id
    assert store.save(receipt) == receipt.receipt_id
    assert JsonSolanaCursorSequenceCheckpointBindingStore(
        tmp_path / "binding.json"
    ).load() == receipt


def test_binding_store_replay_verifies_receipt(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    receipt = advance_and_checkpoint_solana_cursor(
        JsonSolanaSlotCursorStore(tmp_path / "cursor.json"),
        JsonSolanaObservationSequenceStore(tmp_path / "sequence.json"),
        JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json"),
        observations,
    )
    store = JsonSolanaCursorSequenceCheckpointBindingStore(tmp_path / "binding.json")
    store.save(receipt)
    replay = store.replay(receipt)
    assert replay.matches is True
    assert replay.replay_id == store.replay(receipt).replay_id


def test_binding_store_replay_fails_closed_on_mismatch(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    receipt = advance_and_checkpoint_solana_cursor(
        JsonSolanaSlotCursorStore(tmp_path / "cursor.json"),
        JsonSolanaObservationSequenceStore(tmp_path / "sequence.json"),
        JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json"),
        observations,
    )
    store = JsonSolanaCursorSequenceCheckpointBindingStore(tmp_path / "binding.json")
    store.save(receipt)
    with pytest.raises(ValueError, match="does not match"):
        store.replay(
            type(receipt)(
                receipt_id=receipt.receipt_id,
                previous_cursor_id=receipt.previous_cursor_id,
                current_cursor_id=receipt.current_cursor_id,
                sequence_id=receipt.sequence_id,
                checkpoint_id=receipt.checkpoint_id,
                observation_id="different",
            )
        )
