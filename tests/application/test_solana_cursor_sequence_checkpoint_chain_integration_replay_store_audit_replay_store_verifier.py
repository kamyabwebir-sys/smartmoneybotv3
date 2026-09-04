from pathlib import Path

import pytest

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_store import (
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStore,
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt,
)
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store_verifier import (
    verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store,
)
from smart_money.core.ids import deterministic_id


def test_audit_replay_store_verifier_passes(tmp_path: Path):
    schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay.v1"
    replay = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt(
        replay_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay",
            {"original_audit_id": "audit", "schema_version": schema},
        ),
        original_audit_id="audit",
        matches=True,
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStore(
        tmp_path / "replay.json"
    )
    store.save(replay)
    result = verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store(
        store, replay
    )
    assert result.matches is True


def test_audit_replay_store_verifier_fails_closed(tmp_path: Path):
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStore(
        tmp_path / "missing.json"
    )
    with pytest.raises(TypeError, match="audit replay receipt"):
        verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store(
            store, object()  # type: ignore[arg-type]
        )
