from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.dashboard_session_final_recovery_chain_receipt_store import (
    JsonDashboardSessionFinalRecoveryChainReceiptStore,
)
from smart_money.application.dashboard_session_final_recovery_chain_gate import (
    DashboardSessionFinalRecoveryChainReceipt,
)


def _receipt() -> DashboardSessionFinalRecoveryChainReceipt:
    return DashboardSessionFinalRecoveryChainReceipt(
        decision="READY",
        reason_code="FINAL_RECOVERY_CHAIN_VERIFIED",
        chain_id="chain-1",
        replay_verification_id="replay-1",
    )


def test_append_is_idempotent_and_reloads(tmp_path) -> None:
    path = tmp_path / "receipts.json"
    receipt = _receipt()
    store = JsonDashboardSessionFinalRecoveryChainReceiptStore(path)

    assert store.append(receipt) == receipt.receipt_id
    assert store.append(receipt) == receipt.receipt_id
    restored = JsonDashboardSessionFinalRecoveryChainReceiptStore(path)

    assert restored.receipt_count == 1
    assert restored.get(receipt.receipt_id) == receipt
    assert list(restored.iter_receipts()) == [receipt]


def test_hash_corruption_is_rejected(tmp_path) -> None:
    path = tmp_path / "receipts.json"
    store = JsonDashboardSessionFinalRecoveryChainReceiptStore(path)
    store.append(_receipt())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["content_hash"] = "f" * 64
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        JsonDashboardSessionFinalRecoveryChainReceiptStore(path)
