from smart_money.application.dashboard_audit_head_anchor import (
    DashboardAuditHeadAnchor,
)
from smart_money.application.dashboard_audit_recovery_gate import (
    DashboardAuditRecoveryGate,
)
from smart_money.application.dashboard_query_audit_chain import (
    DashboardQueryAuditChain,
)
from smart_money.application.dashboard_query_replay_verifier import (
    DashboardQueryReplayReceipt,
)
from smart_money.application.dashboard_recovery_replay_verifier import (
    DashboardRecoveryReplayVerifier,
)


def _chain() -> DashboardQueryAuditChain:
    return DashboardQueryAuditChain.from_receipts(
        [
            DashboardQueryReplayReceipt(
                query_id="q",
                expected_receipt_id="e",
                actual_receipt_id="a",
                matches=True,
            )
        ]
    )


def test_recovery_replay_matches() -> None:
    chain = _chain()
    anchor = DashboardAuditHeadAnchor.from_chain(chain)
    expected = DashboardAuditRecoveryGate().evaluate(chain, anchor)

    verification = DashboardRecoveryReplayVerifier().verify(
        chain,
        anchor,
        expected,
    )

    assert verification.matches is True
    assert verification.mismatches == ()


def test_recovery_replay_detects_head_drift() -> None:
    chain = _chain()
    expected = DashboardAuditRecoveryGate().evaluate(
        chain,
        DashboardAuditHeadAnchor.from_chain(chain),
    )
    changed_chain = DashboardQueryAuditChain.from_receipts([])

    verification = DashboardRecoveryReplayVerifier().verify(
        changed_chain,
        DashboardAuditHeadAnchor.from_chain(chain),
        expected,
    )

    assert verification.matches is False
    assert "decision" in verification.mismatches
