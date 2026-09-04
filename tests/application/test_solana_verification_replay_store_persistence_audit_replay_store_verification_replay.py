from pathlib import Path

from smart_money.adapters.persistence.solana_verification_replay_store_persistence_audit_replay_store_verification_store import (
    JsonSolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationStore,
)
from smart_money.application.solana_verification_replay_store_persistence_audit_replay_store_verifier import (
    SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt,
)
from smart_money.application.solana_verification_replay_store_persistence_audit_replay_store_verification_replay import (
    replay_verify_solana_verification_replay_store_persistence_audit_replay_store_verification,
)
from smart_money.core.ids import deterministic_id


def test_verification_store_replay_round_trip(tmp_path: Path):
    schema = "solana_verification_replay_store_persistence_audit_replay_store_verification.v1"
    receipt = SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt(
        verification_id=deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay_store_verification",
            {"matches": True, "replay_id": "replay-1", "schema_version": schema},
        ),
        replay_id="replay-1",
        matches=True,
    )
    store = JsonSolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationStore(
        tmp_path / "verification.json"
    )
    store.save(receipt)
    replay = replay_verify_solana_verification_replay_store_persistence_audit_replay_store_verification(
        store, receipt
    )
    assert replay.matches is True
    assert replay.replay_id == receipt.replay_id


def test_verification_store_replay_fails_when_missing(tmp_path: Path):
    store = JsonSolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationStore(
        tmp_path / "missing.json"
    )
    schema = "solana_verification_replay_store_persistence_audit_replay_store_verification.v1"
    receipt = SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt(
        verification_id=deterministic_id(
            "solana_verification_replay_store_persistence_audit_replay_store_verification",
            {"matches": True, "replay_id": "replay-1", "schema_version": schema},
        ),
        replay_id="replay-1",
        matches=True,
    )
    try:
        replay_verify_solana_verification_replay_store_persistence_audit_replay_store_verification(
            store, receipt
        )
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("expected missing receipt failure")
