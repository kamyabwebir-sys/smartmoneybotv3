from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence import (
    dashboard_session_final_recovery_audit_chain_replay_store as replay_store,
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
from smart_money.application.dashboard_session_final_audit_chain import (
    DashboardSessionFinalAuditChain,
)
from smart_money.application.dashboard_session_final_audit_chain_replay_verifier import (
    DashboardSessionFinalAuditChainReplayVerifier,
)
from smart_money.application.dashboard_session_final_audit_recovery_gate import (
    DashboardSessionFinalAuditRecoveryGate,
)
from smart_money.application.dashboard_session_final_audit_recovery_replay_verifier import (
    DashboardSessionFinalAuditRecoveryReplayVerifier,
)
from smart_money.application.dashboard_session_final_recovery_audit_chain import (
    DashboardSessionFinalRecoveryAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_audit_chain_replay_verifier import (
    DashboardSessionFinalRecoveryAuditChainReplayVerifier,
)
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryGate,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayVerifier,
)


def _receipt():
    source = DashboardSessionAuditChain(entries=(), chain_hash="0" * 64)
    anchor = DashboardSessionAuditHeadAnchor.from_chain(source)
    recovery = DashboardSessionRecoveryGate().evaluate(source, anchor)
    recovery_replay = DashboardSessionRecoveryReplayVerifier().verify(
        source, anchor, recovery
    )
    final = DashboardSessionAuditChainFinalizer().finalize(
        source, anchor, recovery, recovery_replay
    )
    final_replay = DashboardSessionAuditFinalReplayVerifier().verify(
        final, source, anchor, recovery, recovery_replay
    )
    final_chain = DashboardSessionFinalAuditChain.from_chain(
        source, final, final_replay
    )
    final_chain_replay = DashboardSessionFinalAuditChainReplayVerifier().verify(
        final_chain, final_chain
    )
    final_recovery = DashboardSessionFinalAuditRecoveryGate().evaluate(
        final_chain, final_chain_replay, final_chain_replay
    )
    final_recovery_replay = (
        DashboardSessionFinalAuditRecoveryReplayVerifier().verify(
            final_recovery,
            final_chain,
            final_chain_replay,
            final_chain_replay,
        )
    )
    chain = DashboardSessionFinalRecoveryAuditChain.from_chain(
        final_chain, final_recovery, final_recovery_replay
    )
    return DashboardSessionFinalRecoveryAuditChainReplayVerifier().verify(
        chain, chain
    )


def test_append_is_idempotent_and_reloads(tmp_path) -> None:
    path = tmp_path / "replay.json"
    receipt = _receipt()
    store = replay_store.JsonDashboardSessionFinalRecoveryAuditChainReplayStore(
        path
    )

    assert store.append(receipt) == receipt.verification_id
    assert store.append(receipt) == receipt.verification_id
    restored = (
        replay_store.JsonDashboardSessionFinalRecoveryAuditChainReplayStore(
            path
        )
    )

    assert restored.receipt_count == 1
    assert restored.get(receipt.verification_id) == receipt
    assert list(restored.iter_receipts()) == [receipt]


def test_hash_corruption_is_rejected(tmp_path) -> None:
    path = tmp_path / "replay.json"
    store = replay_store.JsonDashboardSessionFinalRecoveryAuditChainReplayStore(
        path
    )
    store.append(_receipt())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["content_hash"] = "f" * 64
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        replay_store.JsonDashboardSessionFinalRecoveryAuditChainReplayStore(
            path
        )
