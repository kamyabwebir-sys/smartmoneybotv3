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
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryGate,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayVerifier,
)


def _inputs():
    chain = DashboardSessionAuditChain(entries=(), chain_hash="0" * 64)
    anchor = DashboardSessionAuditHeadAnchor.from_chain(chain)
    recovery = DashboardSessionRecoveryGate().evaluate(chain, anchor)
    replay = DashboardSessionRecoveryReplayVerifier().verify(
        chain, anchor, recovery
    )
    expected = DashboardSessionAuditChainFinalizer().finalize(
        chain, anchor, recovery, replay
    )
    return expected, chain, anchor, recovery, replay


def test_replay_verifier_matches_rebuilt_final_receipt() -> None:
    result = DashboardSessionAuditFinalReplayVerifier().verify(*_inputs())

    assert result.matches is True
    assert result.mismatches == ()
    assert result.expected_receipt_id == result.actual_receipt_id
    assert result.verification_id


def test_replay_verifier_reports_deterministic_field_mismatch() -> None:
    expected, chain, anchor, recovery, replay = _inputs()
    altered = replace(expected, reason_code="ALTERED")

    result = DashboardSessionAuditFinalReplayVerifier().verify(
        altered, chain, anchor, recovery, replay
    )

    assert result.matches is False
    assert result.expected_receipt_id == altered.receipt_id
    assert result.actual_receipt_id == expected.receipt_id
    assert result.mismatches == ("reason_code",)
