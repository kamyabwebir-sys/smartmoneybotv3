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


def test_gate_is_ready_for_matching_head() -> None:
    chain = _chain()
    receipt = DashboardAuditRecoveryGate().evaluate(
        chain,
        DashboardAuditHeadAnchor.from_chain(chain),
    )
    assert receipt.decision == "READY"
    assert receipt.reason_code == "CHAIN_HEAD_VERIFIED"
    assert receipt.receipt_id == DashboardAuditRecoveryGate().evaluate(
        chain,
        DashboardAuditHeadAnchor.from_chain(chain),
    ).receipt_id


def test_gate_blocks_missing_or_mismatched_head() -> None:
    chain = _chain()
    gate = DashboardAuditRecoveryGate()
    missing = gate.evaluate(chain, None)
    mismatch = gate.evaluate(
        chain,
        DashboardAuditHeadAnchor(
            chain_id="other",
            chain_hash="b" * 64,
            receipt_count=0,
            latest_verification_id=None,
        ),
    )
    assert missing.decision == "BLOCKED"
    assert missing.reason_code == "MISSING_CHAIN_OR_ANCHOR"
    assert mismatch.decision == "BLOCKED"
    assert mismatch.reason_code == "CHAIN_HEAD_MISMATCH"
