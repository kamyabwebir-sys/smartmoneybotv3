from pathlib import Path

import pytest

from smart_money.adapters.persistence.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_store import (
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStore,
    JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditStore,
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt,
)
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit import (
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt,
)


def test_audit_store_round_trip_and_idempotent_save(tmp_path: Path):
    receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt(
        expected_replay_id="expected",
        persisted_replay_id=None,
        matches=False,
        file_exists=False,
        mismatches=("persisted replay receipt is missing",),
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditStore(
        tmp_path / "audit.json"
    )
    assert store.save(receipt) == receipt.audit_id
    assert store.save(receipt) == receipt.audit_id
    restored = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditStore(
        tmp_path / "audit.json"
    )
    assert restored.load() == receipt


def test_audit_store_replay_verifies_persisted_audit(tmp_path: Path):
    receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt(
        expected_replay_id="expected",
        persisted_replay_id=None,
        matches=False,
        file_exists=False,
        mismatches=("persisted replay receipt is missing",),
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditStore(
        tmp_path / "audit.json"
    )
    store.save(receipt)
    replay = store.replay(receipt)
    assert replay.matches is True
    assert isinstance(
        replay, SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt
    )


def test_audit_store_replay_fails_closed_on_mismatch(tmp_path: Path):
    receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt(
        expected_replay_id="expected",
        persisted_replay_id=None,
        matches=False,
        file_exists=False,
        mismatches=("persisted replay receipt is missing",),
    )
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditStore(
        tmp_path / "audit.json"
    )
    store.save(receipt)
    mismatch = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt(
        expected_replay_id="other",
        persisted_replay_id=None,
        matches=False,
        file_exists=False,
        mismatches=("persisted replay receipt is missing",),
    )
    with pytest.raises(ValueError, match="does not match"):
        store.replay(mismatch)


def test_audit_replay_store_round_trip_and_idempotent_save(tmp_path: Path):
    audit = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt(
        expected_replay_id="expected",
        persisted_replay_id=None,
        matches=False,
        file_exists=False,
        mismatches=("persisted replay receipt is missing",),
    )
    audit_store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditStore(
        tmp_path / "audit.json"
    )
    audit_store.save(audit)
    replay = audit_store.replay(audit)
    store = JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStore(
        tmp_path / "audit-replay.json"
    )
    assert store.save(replay) == replay.replay_id
    assert store.save(replay) == replay.replay_id
    assert store.load() == replay
