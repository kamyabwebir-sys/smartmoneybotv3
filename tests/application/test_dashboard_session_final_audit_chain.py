from __future__ import annotations

import pytest

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
    recovery_replay = DashboardSessionRecoveryReplayVerifier().verify(
        chain, anchor, recovery
    )
    final = DashboardSessionAuditChainFinalizer().finalize(
        chain, anchor, recovery, recovery_replay
    )
    final_replay = DashboardSessionAuditFinalReplayVerifier().verify(
        final, chain, anchor, recovery, recovery_replay
    )
    return chain, final, final_replay


def test_final_chain_integrates_final_and_replay_receipts() -> None:
    chain, final, final_replay = _inputs()

    integrated = DashboardSessionFinalAuditChain.from_chain(
        chain, final, final_replay
    )

    assert len(integrated.entries) == 2
    assert integrated.entries[-2].entry_kind == "final"
    assert integrated.entries[-1].entry_kind == "final_replay"
    assert integrated.entries[-1].parent_id == final.receipt_id
    assert integrated.chain_id


def test_final_chain_rejects_non_matching_replay() -> None:
    chain, final, final_replay = _inputs()
    mismatch = type(final_replay)(
        expected_receipt_id=final_replay.expected_receipt_id,
        actual_receipt_id="different",
        matches=False,
        mismatches=("actual_receipt_id",),
    )

    with pytest.raises(ValueError, match="non-matching final replay"):
        DashboardSessionFinalAuditChain.from_chain(chain, final, mismatch)
