from pathlib import Path

import pytest

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_store import (
    JsonSolanaCursorSequenceCheckpointStore,
)
from smart_money.adapters.persistence.solana_observation_sequence_store import (
    JsonSolanaObservationSequenceStore,
)
from smart_money.adapters.persistence.solana_slot_cursor_store import JsonSolanaSlotCursorStore
from smart_money.application.solana_cursor_sequence_checkpoint_binding import (
    advance_and_checkpoint_solana_cursor,
    verify_solana_cursor_sequence_checkpoint_binding_replay,
)
from tests.domain.test_solana_observation import _observation


def test_advance_and_checkpoint_binds_all_stores(tmp_path: Path):
    observations = (
        _observation(slot=1, observed_at=10, transaction_signature="a"),
        _observation(slot=2, observed_at=11, transaction_signature="b"),
    )
    cursor_store = JsonSolanaSlotCursorStore(tmp_path / "cursor.json")
    sequence_store = JsonSolanaObservationSequenceStore(tmp_path / "sequence.json")
    checkpoint_store = JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json")
    receipt = advance_and_checkpoint_solana_cursor(
        cursor_store, sequence_store, checkpoint_store, observations
    )
    assert receipt.sequence_id == next(iter(sequence_store.iter_receipts())).sequence_id
    assert receipt.current_cursor_id == cursor_store.cursor_id
    assert receipt.checkpoint_id == checkpoint_store.checkpoint_id


def test_binding_receipt_is_deterministic(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    first_stores = (
        JsonSolanaSlotCursorStore(tmp_path / "cursor.json"),
        JsonSolanaObservationSequenceStore(tmp_path / "sequence.json"),
        JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json"),
    )
    first = advance_and_checkpoint_solana_cursor(*first_stores, observations)
    second_stores = (
        JsonSolanaSlotCursorStore(tmp_path / "cursor-2.json"),
        JsonSolanaObservationSequenceStore(tmp_path / "sequence-2.json"),
        JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint-2.json"),
    )
    second = advance_and_checkpoint_solana_cursor(*second_stores, observations)
    assert first == second


def test_binding_replay_verifies_all_persisted_components(tmp_path: Path):
    observations = (
        _observation(slot=1, observed_at=10, transaction_signature="a"),
        _observation(slot=2, observed_at=11, transaction_signature="b"),
    )
    stores = (
        JsonSolanaSlotCursorStore(tmp_path / "cursor.json"),
        JsonSolanaObservationSequenceStore(tmp_path / "sequence.json"),
        JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json"),
    )
    receipt = advance_and_checkpoint_solana_cursor(*stores, observations)
    replay = verify_solana_cursor_sequence_checkpoint_binding_replay(
        *stores, observations, receipt
    )
    assert replay.matches is True


def test_binding_replay_fails_closed_on_changed_observations(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    stores = (
        JsonSolanaSlotCursorStore(tmp_path / "cursor.json"),
        JsonSolanaObservationSequenceStore(tmp_path / "sequence.json"),
        JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json"),
    )
    receipt = advance_and_checkpoint_solana_cursor(*stores, observations)
    with pytest.raises(ValueError, match="sequence"):
        verify_solana_cursor_sequence_checkpoint_binding_replay(
            *stores,
            (_observation(slot=2, observed_at=11, transaction_signature="b"),),
            receipt,
        )
