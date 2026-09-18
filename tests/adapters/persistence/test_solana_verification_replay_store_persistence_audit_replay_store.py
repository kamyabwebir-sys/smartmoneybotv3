from pathlib import Path

from smart_money.adapters.persistence.solana_verification_replay_store_persistence_audit_replay_store import (
    JsonSolanaVerificationReplayStorePersistenceAuditReplayStore,
)
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store_audit import (
    SolanaVerificationReplayStorePersistenceAuditReplayReceipt,
)
from smart_money.core.ids import deterministic_id


def test_audit_replay_persistence_store_round_trip(tmp_path: Path):
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
        tmp_path / "audit-replay.json"
    )
    assert store.save(receipt) == receipt.replay_id
    assert store.save(receipt) == receipt.replay_id
    assert JsonSolanaVerificationReplayStorePersistenceAuditReplayStore(
        tmp_path / "audit-replay.json"
    ).load() == receipt
