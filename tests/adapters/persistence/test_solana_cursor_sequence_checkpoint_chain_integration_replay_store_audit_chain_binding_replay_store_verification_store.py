from pathlib import Path

import pytest

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_store import (
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore,
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationStore,
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt,
)
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verifier import (
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


def test_verification_store_round_trip(tmp_path: Path):
    schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification.v1"
    receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReceipt(
        verification_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification",
            {"matches": True, "replay_id": "replay", "schema_version": schema},
        ),
        replay_id="replay",
        matches=True,
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationStore(
        tmp_path / "verification.json"
    )
    assert store.save(receipt) == receipt.verification_id
    assert store.save(receipt) == receipt.verification_id
    assert JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationStore(
        tmp_path / "verification.json"
    ).load() == receipt


def test_verification_store_replay(tmp_path: Path):
    schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification.v1"
    receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReceipt(
        verification_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification",
            {"matches": True, "replay_id": "replay", "schema_version": schema},
        ),
        replay_id="replay",
        matches=True,
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationStore(
        tmp_path / "verification.json"
    )
    store.save(receipt)
    replay = store.replay(receipt)
    assert replay.matches is True


def test_verification_store_replay_fails_closed(tmp_path: Path):
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationStore(
        tmp_path / "missing.json"
    )
    with pytest.raises(ValueError, match="missing"):
        store.replay(object())


def test_verification_replay_store_round_trip(tmp_path: Path):
    schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay.v1"
    receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt(
        replay_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay",
            {"original_verification_id": "verification", "schema_version": schema},
        ),
        original_verification_id="verification",
        matches=True,
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore(
        tmp_path / "replay.json"
    )
    assert store.save(receipt) == receipt.replay_id
    assert store.save(receipt) == receipt.replay_id
    assert JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore(
        tmp_path / "replay.json"
    ).load() == receipt
