from pathlib import Path

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_store import (
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore,
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt,
)
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store_audit import (
    SolanaVerificationReplayStorePersistenceAuditReceipt,
    audit_solana_verification_replay_store_persistence,
    replay_solana_verification_replay_store_persistence_audit,
)
from smart_money.core.ids import deterministic_id


def test_verification_replay_store_persistence_audit(tmp_path: Path):
    schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay.v1"
    replay = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt(
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
    store.save(replay)
    audit = audit_solana_verification_replay_store_persistence(store, replay)
    assert audit.matches is True
    assert audit.file_exists is True


def test_verification_replay_store_persistence_audit_replay():
    audit = SolanaVerificationReplayStorePersistenceAuditReceipt(
        expected_replay_id="expected",
        persisted_replay_id="expected",
        file_exists=True,
        matches=True,
    )
    replay = replay_solana_verification_replay_store_persistence_audit(audit, audit)
    assert replay.matches is True
