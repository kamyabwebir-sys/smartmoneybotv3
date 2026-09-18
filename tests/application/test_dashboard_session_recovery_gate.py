from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
)
from smart_money.application.dashboard_session_audit_head_anchor import (
    DashboardSessionAuditHeadAnchor,
)
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryGate,
)


def test_session_gate_blocks_missing_chain() -> None:
    receipt = DashboardSessionRecoveryGate().evaluate(None, None)
    assert receipt.decision == "BLOCKED"
    assert receipt.reason_code == "MISSING_SESSION_CHAIN_OR_ANCHOR"


def test_session_gate_ready_for_matching_head() -> None:
    chain = DashboardSessionAuditChain(
        entries=(),
        chain_hash="0" * 64,
    )
    anchor = DashboardSessionAuditHeadAnchor.from_chain(chain)
    receipt = DashboardSessionRecoveryGate().evaluate(chain, anchor)
    assert receipt.decision == "READY"
    assert receipt.reason_code == "SESSION_CHAIN_HEAD_VERIFIED"
