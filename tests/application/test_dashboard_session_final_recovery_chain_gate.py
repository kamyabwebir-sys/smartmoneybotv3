from __future__ import annotations

from dataclasses import replace

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
from smart_money.application.dashboard_session_final_recovery_chain_gate import (
    DashboardSessionFinalRecoveryChainGate,
)
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryGate,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayVerifier,
)


def _inputs():
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
    replay = DashboardSessionFinalRecoveryAuditChainReplayVerifier().verify(
        chain, chain
    )
    return chain, replay


def test_gate_returns_ready_for_verified_persisted_replay() -> None:
    chain, replay = _inputs()

    result = DashboardSessionFinalRecoveryChainGate().evaluate(
        chain, replay, replay
    )

    assert result.decision == "READY"
    assert result.reason_code == "FINAL_RECOVERY_CHAIN_VERIFIED"
    assert result.chain_id == chain.chain_id
    assert result.replay_verification_id == replay.verification_id


def test_gate_fails_closed_on_persisted_replay_mismatch() -> None:
    chain, replay = _inputs()
    altered = replace(replay, actual_chain_id="different")

    result = DashboardSessionFinalRecoveryChainGate().evaluate(
        chain, replay, altered
    )

    assert result.decision == "BLOCKED"
    assert result.reason_code == "PERSISTED_FINAL_RECOVERY_REPLAY_MISMATCH"


def test_gate_fails_closed_when_inputs_missing() -> None:
    result = DashboardSessionFinalRecoveryChainGate().evaluate(None, None, None)

    assert result.decision == "BLOCKED"
    assert result.reason_code == "MISSING_FINAL_RECOVERY_CHAIN_OR_REPLAY"
