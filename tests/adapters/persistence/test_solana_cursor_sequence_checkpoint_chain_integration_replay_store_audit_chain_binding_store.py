from pathlib import Path

import pytest

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_store import (
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStore,
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingStore,
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayReceipt,
)
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding import (
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt,
)
from smart_money.core.ids import deterministic_id


def test_audit_chain_binding_store_round_trip_and_idempotent_save(tmp_path: Path):
    schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding.v1"
    binding = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt(
        binding_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding",
            {
                "matches": True,
                "prior_audit_id": "audit",
                "schema_version": schema,
                "verification_id": "verification",
            },
        ),
        verification_id="verification",
        prior_audit_id="audit",
        matches=True,
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingStore(
        tmp_path / "binding.json"
    )
    assert store.save(binding) == binding.binding_id
    assert store.save(binding) == binding.binding_id
    restored = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingStore(
        tmp_path / "binding.json"
    )
    assert restored.load() == binding


def test_audit_chain_binding_replay_verifies(tmp_path: Path):
    schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding.v1"
    binding = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt(
        binding_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding",
            {"matches": True, "prior_audit_id": "audit", "schema_version": schema, "verification_id": "verification"},
        ),
        verification_id="verification",
        prior_audit_id="audit",
        matches=True,
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingStore(
        tmp_path / "binding.json"
    )
    store.save(binding)
    assert store.replay(binding).matches is True


def test_audit_chain_binding_replay_missing_fails_closed(tmp_path: Path):
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingStore(
        tmp_path / "missing.json"
    )
    with pytest.raises(ValueError, match="missing"):
        store.replay(object())


def test_audit_chain_binding_replay_persistence_round_trip(tmp_path: Path):
    schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay.v1"
    replay = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayReceipt(
        replay_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay",
            {"original_binding_id": "binding", "schema_version": schema},
        ),
        original_binding_id="binding",
        matches=True,
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStore(
        tmp_path / "replay.json"
    )
    assert store.save(replay) == replay.replay_id
    assert store.save(replay) == replay.replay_id
    restored = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStore(
        tmp_path / "replay.json"
    )
    assert restored.load() == replay
