from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence import (
    dashboard_session_final_recovery_gate_audit_chain_replay_store as chain_store,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_chain_replay_verifier as replay_model,
)


def _receipt() -> replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayReceipt:
    return replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayReceipt(
        expected_chain_id="expected-chain",
        actual_chain_id="actual-chain",
        expected_chain_hash="0" * 64,
        actual_chain_hash="0" * 64,
        expected_entry_count=0,
        actual_entry_count=0,
        matches=True,
    )


def test_append_is_idempotent_and_reloads(tmp_path) -> None:
    path = tmp_path / "replay.json"
    receipt = _receipt()
    store = chain_store.JsonDashboardSessionFinalRecoveryGateAuditChainReplayStore(
        path
    )

    assert store.append(receipt) == receipt.verification_id
    assert store.append(receipt) == receipt.verification_id
    restored = (
        chain_store.JsonDashboardSessionFinalRecoveryGateAuditChainReplayStore(
            path
        )
    )

    assert restored.receipt_count == 1
    assert restored.get(receipt.verification_id) == receipt
    assert list(restored.iter_receipts()) == [receipt]


def test_hash_corruption_is_rejected(tmp_path) -> None:
    path = tmp_path / "replay.json"
    store = chain_store.JsonDashboardSessionFinalRecoveryGateAuditChainReplayStore(
        path
    )
    store.append(_receipt())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["content_hash"] = "f" * 64
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        chain_store.JsonDashboardSessionFinalRecoveryGateAuditChainReplayStore(
            path
        )
