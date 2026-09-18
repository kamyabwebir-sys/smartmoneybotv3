from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.dashboard_session_final_recovery_chain_replay_store import (
    JsonDashboardSessionFinalRecoveryChainReplayStore,
)
from smart_money.application.dashboard_session_final_recovery_chain_replay_verifier import (
    DashboardSessionFinalRecoveryChainReplayReceipt,
)


def _receipt() -> DashboardSessionFinalRecoveryChainReplayReceipt:
    return DashboardSessionFinalRecoveryChainReplayReceipt(
        expected_receipt_id="expected-1",
        actual_receipt_id="actual-1",
        matches=True,
    )


def test_append_is_idempotent_and_reloads(tmp_path) -> None:
    path = tmp_path / "replay.json"
    receipt = _receipt()
    store = JsonDashboardSessionFinalRecoveryChainReplayStore(path)

    assert store.append(receipt) == receipt.verification_id
    assert store.append(receipt) == receipt.verification_id
    restored = JsonDashboardSessionFinalRecoveryChainReplayStore(path)

    assert restored.receipt_count == 1
    assert restored.get(receipt.verification_id) == receipt
    assert list(restored.iter_receipts()) == [receipt]


def test_hash_corruption_is_rejected(tmp_path) -> None:
    path = tmp_path / "replay.json"
    store = JsonDashboardSessionFinalRecoveryChainReplayStore(path)
    store.append(_receipt())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["content_hash"] = "f" * 64
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        JsonDashboardSessionFinalRecoveryChainReplayStore(path)
