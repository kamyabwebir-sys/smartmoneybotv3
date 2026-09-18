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
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration import (
    integrate_solana_cursor_sequence_checkpoint_chain,
)
from tests.domain.test_solana_observation import _observation


def _stores(tmp_path: Path):
    return (
        JsonSolanaSlotCursorStore(tmp_path / "cursor.json"),
        JsonSolanaObservationSequenceStore(tmp_path / "sequence.json"),
        JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json"),
        JsonSolanaCursorSequenceCheckpointBindingStore(tmp_path / "binding.json"),
    )


def test_chain_integration_binds_all_persisted_layers(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    cursor, sequence, checkpoint, binding = _stores(tmp_path)
    receipt = advance_and_checkpoint_solana_cursor(cursor, sequence, checkpoint, observations)
    binding.save(receipt)
    integrated = integrate_solana_cursor_sequence_checkpoint_chain(
        cursor, sequence, checkpoint, binding, observations, receipt
    )
    assert integrated.sequence_id == receipt.sequence_id
    assert integrated.checkpoint_id == receipt.checkpoint_id
    assert integrated.binding_receipt_id == receipt.receipt_id


def test_chain_integration_fails_closed_on_wrong_binding(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    cursor, sequence, checkpoint, binding = _stores(tmp_path)
    receipt = advance_and_checkpoint_solana_cursor(cursor, sequence, checkpoint, observations)
    binding.save(receipt)
    with pytest.raises(ValueError, match="deterministic payload"):
        integrate_solana_cursor_sequence_checkpoint_chain(
            cursor, sequence, checkpoint, binding, observations,
            type(receipt)(
                receipt_id=receipt.receipt_id,
                previous_cursor_id=receipt.previous_cursor_id,
                current_cursor_id=receipt.current_cursor_id,
                sequence_id=receipt.sequence_id,
                checkpoint_id=receipt.checkpoint_id,
                observation_id="wrong",
            ),
        )
