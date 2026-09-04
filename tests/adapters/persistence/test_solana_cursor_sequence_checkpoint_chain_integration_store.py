from pathlib import Path

import pytest

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_binding_store import (
    JsonSolanaCursorSequenceCheckpointBindingStore,
)
from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_store import (  # noqa: E501
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStore,
    JsonSolanaCursorSequenceCheckpointChainIntegrationStore,
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
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration import (
    integrate_solana_cursor_sequence_checkpoint_chain,
)
from tests.domain.test_solana_observation import _observation


def test_chain_integration_store_round_trip_and_idempotent_save(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    cursor = JsonSolanaSlotCursorStore(tmp_path / "cursor.json")
    sequence = JsonSolanaObservationSequenceStore(tmp_path / "sequence.json")
    checkpoint = JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json")
    binding = JsonSolanaCursorSequenceCheckpointBindingStore(tmp_path / "binding.json")
    binding_receipt = advance_and_checkpoint_solana_cursor(
        cursor, sequence, checkpoint, observations
    )
    binding.save(binding_receipt)
    receipt = integrate_solana_cursor_sequence_checkpoint_chain(
        cursor, sequence, checkpoint, binding, observations, binding_receipt
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationStore(
        tmp_path / "integration.json"
    )
    assert store.save(receipt) == receipt.receipt_id
    assert store.save(receipt) == receipt.receipt_id
    restored = JsonSolanaCursorSequenceCheckpointChainIntegrationStore(
        tmp_path / "integration.json"
    )
    assert restored.load() == receipt


def test_chain_integration_store_replay_verifies_receipt(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    cursor = JsonSolanaSlotCursorStore(tmp_path / "cursor.json")
    sequence = JsonSolanaObservationSequenceStore(tmp_path / "sequence.json")
    checkpoint = JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json")
    binding = JsonSolanaCursorSequenceCheckpointBindingStore(tmp_path / "binding.json")
    binding_receipt = advance_and_checkpoint_solana_cursor(
        cursor, sequence, checkpoint, observations
    )
    binding.save(binding_receipt)
    receipt = integrate_solana_cursor_sequence_checkpoint_chain(
        cursor, sequence, checkpoint, binding, observations, binding_receipt
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationStore(
        tmp_path / "integration.json"
    )
    store.save(receipt)
    replay = store.replay(receipt)
    assert replay.matches is True
    assert replay.replay_id == store.replay(receipt).replay_id


def test_chain_integration_store_replay_fails_closed_on_mismatch(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    cursor = JsonSolanaSlotCursorStore(tmp_path / "cursor.json")
    sequence = JsonSolanaObservationSequenceStore(tmp_path / "sequence.json")
    checkpoint = JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json")
    binding = JsonSolanaCursorSequenceCheckpointBindingStore(tmp_path / "binding.json")
    binding_receipt = advance_and_checkpoint_solana_cursor(
        cursor, sequence, checkpoint, observations
    )
    binding.save(binding_receipt)
    receipt = integrate_solana_cursor_sequence_checkpoint_chain(
        cursor, sequence, checkpoint, binding, observations, binding_receipt
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationStore(
        tmp_path / "integration.json"
    )
    store.save(receipt)
    with pytest.raises(ValueError, match="does not match"):
        store.replay(
            type(receipt)(
                receipt_id=receipt.receipt_id,
                sequence_id=receipt.sequence_id,
                checkpoint_id=receipt.checkpoint_id,
                binding_receipt_id=receipt.binding_receipt_id,
                cursor_id=receipt.cursor_id,
                observation_id="different",
            )
        )


def test_chain_integration_replay_receipt_store_round_trip(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    cursor = JsonSolanaSlotCursorStore(tmp_path / "cursor.json")
    sequence = JsonSolanaObservationSequenceStore(tmp_path / "sequence.json")
    checkpoint = JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json")
    binding = JsonSolanaCursorSequenceCheckpointBindingStore(tmp_path / "binding.json")
    binding_receipt = advance_and_checkpoint_solana_cursor(
        cursor, sequence, checkpoint, observations
    )
    binding.save(binding_receipt)
    integrated = integrate_solana_cursor_sequence_checkpoint_chain(
        cursor, sequence, checkpoint, binding, observations, binding_receipt
    )
    replay = JsonSolanaCursorSequenceCheckpointChainIntegrationStore(
        tmp_path / "integration.json"
    )
    replay.save(integrated)
    replay_receipt = replay.replay(integrated)
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStore(
        tmp_path / "replay.json"
    )
    assert store.save(replay_receipt) == replay_receipt.replay_id
    assert store.load() == replay_receipt
