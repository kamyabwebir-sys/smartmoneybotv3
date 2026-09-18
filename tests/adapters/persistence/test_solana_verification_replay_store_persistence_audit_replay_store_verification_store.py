from pathlib import Path

from smart_money.adapters.persistence.solana_verification_replay_store_persistence_audit_replay_store_verification_store import (
    JsonSolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationStore,
)
from smart_money.application.solana_verification_replay_store_persistence_audit_replay_store_verifier import (
    SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


def test_verification_receipt_store_round_trip(tmp_path: Path):
    schema = "solana_verification_replay_store_persistence_audit_replay_store_verification.v1"
    receipt = SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt(
        verification_id=deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay_store_verification",
            {"matches": True, "replay_id": "replay-1", "schema_version": schema},
        ),
        replay_id="replay-1",
        matches=True,
    )
    path = tmp_path / "verification.json"
    store = JsonSolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationStore(path)
    assert store.save(receipt) == receipt.verification_id
    assert store.save(receipt) == receipt.verification_id
    restored = (
        JsonSolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationStore(path)
    )
    assert restored.load() == receipt


def test_verification_receipt_store_rejects_identity_collision(tmp_path: Path):
    schema = "solana_verification_replay_store_persistence_audit_replay_store_verification.v1"
    first = SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt(
        verification_id=deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay_store_verification",
            {"matches": True, "replay_id": "replay-1", "schema_version": schema},
        ),
        replay_id="replay-1",
        matches=True,
    )
    second = SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt(
        verification_id=deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay_store_verification",
            {"matches": False, "replay_id": "replay-2", "schema_version": schema},
        ),
        replay_id="replay-2",
        matches=False,
    )
    store = JsonSolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationStore(
        tmp_path / "verification.json"
    )
    store.save(first)
    try:
        store.save(second)
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected identity collision")
