from pathlib import Path

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_store import (
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStore,
    SolanaCursorSequenceCheckpointChainIntegrationReplayReceipt,
)
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit import (
    audit_solana_cursor_sequence_checkpoint_chain_integration_replay_store,
)
from smart_money.core.ids import deterministic_id


def test_audit_missing_store_fails_closed(tmp_path: Path):
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStore(
        tmp_path / "missing.json"
    )
    schema = "solana_cursor_sequence_checkpoint_chain_integration_replay.v1"
    expected = SolanaCursorSequenceCheckpointChainIntegrationReplayReceipt(
        replay_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay",
            {"original_receipt_id": "y", "schema_version": schema},
        ),
        original_receipt_id="y",
        matches=True,
    )
    audit = audit_solana_cursor_sequence_checkpoint_chain_integration_replay_store(
        store, expected
    )
    assert audit.matches is False
    assert audit.file_exists is False
