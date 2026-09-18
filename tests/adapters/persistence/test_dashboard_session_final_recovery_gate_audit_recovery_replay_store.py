from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence import (
    dashboard_session_final_recovery_gate_audit_recovery_replay_store as replay_store,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_recovery_replay_verifier as replay_verifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditChainReplayVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_gate import (
    DashboardSessionFinalRecoveryGateAuditRecoveryGate,
)


def _receipt() -> replay_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt:
    chain = DashboardSessionFinalRecoveryGateAuditChain(
        entries=(),
        chain_hash="0" * 64,
    )
    chain_replay = DashboardSessionFinalRecoveryGateAuditChainReplayVerifier().verify(
        chain, chain
    )
    recovery = DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
        chain, chain_replay, chain_replay
    )
    return replay_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier().verify(
        recovery, chain, chain_replay, chain_replay
    )


def test_append_is_idempotent_and_reloads(tmp_path) -> None:
    path = tmp_path / "recovery_replay_store.json"
    store = replay_store.JsonDashboardSessionFinalRecoveryGateAuditRecoveryReplayStore(path)
    receipt = _receipt()

    assert store.append(receipt) == receipt.verification_id
    assert store.append(receipt) == receipt.verification_id

    restored = replay_store.JsonDashboardSessionFinalRecoveryGateAuditRecoveryReplayStore(
        path
    )
    assert restored.receipt_count == 1
    assert restored.get(receipt.verification_id) == receipt
    assert list(restored.iter_receipts()) == [receipt]


def test_hash_corruption_is_rejected(tmp_path) -> None:
    path = tmp_path / "recovery_replay_store.json"
    store = replay_store.JsonDashboardSessionFinalRecoveryGateAuditRecoveryReplayStore(path)
    store.append(_receipt())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["content_hash"] = "f" * 64
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        replay_store.JsonDashboardSessionFinalRecoveryGateAuditRecoveryReplayStore(path)
