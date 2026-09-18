from pathlib import Path

import pytest

from smart_money.adapters.persistence.solana_verification_replay_store_persistence_audit_replay_store import (
    JsonSolanaVerificationReplayStorePersistenceAuditReplayStore,
)
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store_audit import (
    SolanaVerificationReplayStorePersistenceAuditReplayReceipt,
)
from smart_money.application.solana_verification_replay_store_persistence_audit_replay_store_verifier import (
    verify_solana_verification_replay_store_persistence_audit_replay_store,
)
from smart_money.core.ids import deterministic_id


def test_verifier_passes(tmp_path: Path):
    schema = "solana_verification_replay_store_persistence_audit_replay.v1"
    receipt = SolanaVerificationReplayStorePersistenceAuditReplayReceipt(
        replay_id=deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay",
            {"original_audit_id": "audit", "schema_version": schema},
        ),
        original_audit_id="audit",
        matches=True,
    )
    store = JsonSolanaVerificationReplayStorePersistenceAuditReplayStore(
        tmp_path / "replay.json"
    )
    store.save(receipt)
    result = verify_solana_verification_replay_store_persistence_audit_replay_store(
        store, receipt
    )
    assert result.matches is True


def test_verifier_fails_closed(tmp_path: Path):
    store = JsonSolanaVerificationReplayStorePersistenceAuditReplayStore(
        tmp_path / "missing.json"
    )
    with pytest.raises(TypeError, match="verification audit replay audit receipt"):
        verify_solana_verification_replay_store_persistence_audit_replay_store(
            store, object()
        )
