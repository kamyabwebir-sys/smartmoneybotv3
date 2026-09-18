from pathlib import Path

import pytest

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_binding_store import (
    JsonSolanaCursorSequenceCheckpointBindingStore,
)
from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_store import (
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
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_verifier import (
    verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store,
)
from tests.domain.test_solana_observation import _observation


def test_replay_store_verifier_passes(tmp_path: Path):
    observations = (_observation(slot=1, observed_at=10, transaction_signature="a"),)
    cursor = JsonSolanaSlotCursorStore(tmp_path / "cursor.json")
    sequence = JsonSolanaObservationSequenceStore(tmp_path / "sequence.json")
    checkpoint = JsonSolanaCursorSequenceCheckpointStore(tmp_path / "checkpoint.json")
    binding = JsonSolanaCursorSequenceCheckpointBindingStore(tmp_path / "binding.json")
    binding_receipt = advance_and_checkpoint_solana_cursor(cursor, sequence, checkpoint, observations)
    binding.save(binding_receipt)
    integrated = integrate_solana_cursor_sequence_checkpoint_chain(
        cursor, sequence, checkpoint, binding, observations, binding_receipt
    )
    integration_store = JsonSolanaCursorSequenceCheckpointChainIntegrationStore(
        tmp_path / "integration.json"
    )
    integration_store.save(integrated)
    replay = integration_store.replay(integrated)
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStore(
        tmp_path / "replay.json"
    )
    store.save(replay)
    result = verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store(
        store, replay
    )
    assert result.matches is True


def test_replay_store_verifier_fails_closed(tmp_path: Path):
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStore(
        tmp_path / "missing.json"
    )
    with pytest.raises(TypeError, match="replay receipt"):
        verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store(
            store, object()  # type: ignore[arg-type]
        )
