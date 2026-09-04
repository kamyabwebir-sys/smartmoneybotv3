from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.dashboard_session_final_recovery_audit_chain_store import (
    JsonDashboardSessionFinalRecoveryAuditChainStore,
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
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryGate,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayVerifier,
)


def _chain() -> DashboardSessionFinalRecoveryAuditChain:
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
    return DashboardSessionFinalRecoveryAuditChain.from_chain(
        final_chain, final_recovery, final_recovery_replay
    )


def test_append_is_idempotent_and_reloads(tmp_path) -> None:
    path = tmp_path / "chain.json"
    chain = _chain()
    store = JsonDashboardSessionFinalRecoveryAuditChainStore(path)

    assert store.append(chain) == chain.chain_id
    assert store.append(chain) == chain.chain_id
    restored = JsonDashboardSessionFinalRecoveryAuditChainStore(path)

    assert restored.chain_count == 1
    assert restored.get(chain.chain_id) == chain
    assert list(restored.iter_chains()) == [chain]


def test_hash_corruption_is_rejected(tmp_path) -> None:
    path = tmp_path / "chain.json"
    store = JsonDashboardSessionFinalRecoveryAuditChainStore(path)
    store.append(_chain())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["content_hash"] = "f" * 64
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        JsonDashboardSessionFinalRecoveryAuditChainStore(path)
