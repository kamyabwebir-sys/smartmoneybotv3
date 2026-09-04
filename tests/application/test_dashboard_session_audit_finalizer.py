from __future__ import annotations

from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
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


def _ready_inputs():
    chain = DashboardSessionAuditChain(entries=(), chain_hash="0" * 64)
    anchor = DashboardSessionAuditHeadAnchor.from_chain(chain)
    recovery = DashboardSessionRecoveryGate().evaluate(chain, anchor)
    replay = DashboardSessionRecoveryReplayVerifier().verify(
        chain, anchor, recovery
    )
    return chain, anchor, recovery, replay


def test_finalizer_produces_deterministic_ready_receipt() -> None:
    inputs = _ready_inputs()
    first = DashboardSessionAuditChainFinalizer().finalize(*inputs)
    second = DashboardSessionAuditChainFinalizer().finalize(*inputs)

    assert first.decision == "READY"
    assert first.reason_code == "SESSION_AUDIT_CHAIN_FINALIZED"
    assert first.receipt_id == second.receipt_id
    assert first.entry_count == 0


def test_finalizer_fails_closed_on_replay_mismatch() -> None:
    chain, anchor, recovery, replay = _ready_inputs()
    mismatch = type(replay)(
        expected_receipt_id=replay.expected_receipt_id,
        actual_receipt_id="different",
        matches=False,
        mismatches=("actual_receipt_id",),
    )

    result = DashboardSessionAuditChainFinalizer().finalize(
        chain, anchor, recovery, mismatch
    )

    assert result.decision == "BLOCKED"
    assert result.reason_code == "SESSION_RECOVERY_REPLAY_MISMATCH"


def test_finalizer_fails_closed_on_missing_anchor() -> None:
    chain, _, recovery, replay = _ready_inputs()

    result = DashboardSessionAuditChainFinalizer().finalize(
        chain, None, recovery, replay
    )

    assert result.decision == "BLOCKED"
    assert result.reason_code == "MISSING_SESSION_CHAIN_OR_ANCHOR"
