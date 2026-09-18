from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.dashboard_session_audit_final_replay_store import (
    JsonDashboardSessionAuditFinalReplayStore,
)
from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
)
from smart_money.application.dashboard_session_audit_final_replay_verifier import (
    DashboardSessionAuditFinalReplayVerifier,
)
from smart_money.application.dashboard_session_audit_finalizer import (
    DashboardSessionAuditChainFinalizer,
)
from smart_money.application.dashboard_session_audit_head_anchor import (
    DashboardSessionAuditHeadAnchor,
)
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryGate,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayVerifier,
)


def _receipt():
    chain = DashboardSessionAuditChain(entries=(), chain_hash="0" * 64)
    anchor = DashboardSessionAuditHeadAnchor.from_chain(chain)
    recovery = DashboardSessionRecoveryGate().evaluate(chain, anchor)
    replay = DashboardSessionRecoveryReplayVerifier().verify(
        chain, anchor, recovery
    )
    final = DashboardSessionAuditChainFinalizer().finalize(
        chain, anchor, recovery, replay
    )
    return DashboardSessionAuditFinalReplayVerifier().verify(
        final, chain, anchor, recovery, replay
    )


def test_append_is_idempotent_and_reloads(tmp_path) -> None:
    path = tmp_path / "replay.json"
    receipt = _receipt()
    store = JsonDashboardSessionAuditFinalReplayStore(path)

    assert store.append(receipt) == receipt.verification_id
    assert store.append(receipt) == receipt.verification_id
    restored = JsonDashboardSessionAuditFinalReplayStore(path)

    assert restored.receipt_count == 1
    assert restored.get(receipt.verification_id) == receipt
    assert list(restored.iter_receipts()) == [receipt]


def test_hash_corruption_is_rejected(tmp_path) -> None:
    path = tmp_path / "replay.json"
    store = JsonDashboardSessionAuditFinalReplayStore(path)
    store.append(_receipt())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["content_hash"] = "f" * 64
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        JsonDashboardSessionAuditFinalReplayStore(path)
