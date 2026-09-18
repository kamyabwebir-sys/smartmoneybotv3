from pathlib import Path

import pytest

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_store import (
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore,
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt,
)
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verifier import (
    verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store,
)
from smart_money.core.ids import deterministic_id


def test_verification_replay_store_verifier_passes(tmp_path: Path):
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
    store.save(receipt)
    result = verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store(
        store, receipt
    )
    assert result.matches is True


def test_verification_replay_store_verifier_fails_closed(tmp_path: Path):
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore(
        tmp_path / "missing.json"
    )
    with pytest.raises(TypeError, match="verification replay receipt"):
        verify_solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store(
            store, object()  # type: ignore[arg-type]
        )
