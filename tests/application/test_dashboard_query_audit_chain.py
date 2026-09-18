import pytest

from smart_money.application.dashboard_query_audit_chain import (
    DashboardQueryAuditChain,
    DashboardQueryAuditChainVerifier,
)
from smart_money.application.dashboard_query_replay_verifier import (
    DashboardQueryReplayReceipt,
)


def _receipt(number: int) -> DashboardQueryReplayReceipt:
    return DashboardQueryReplayReceipt(
        query_id=f"query-{number}",
        expected_receipt_id=f"expected-{number}",
        actual_receipt_id=f"actual-{number}",
        matches=True,
    )


def test_audit_chain_is_deterministic_and_verifiable() -> None:
    receipts = [_receipt(1), _receipt(2)]
    chain = DashboardQueryAuditChain.from_receipts(receipts)

    assert chain.chain_id == DashboardQueryAuditChain.from_receipts(
        receipts
    ).chain_id
    assert DashboardQueryAuditChainVerifier().verify(chain, receipts) is True


def test_audit_chain_detects_reordering_or_removal() -> None:
    receipts = [_receipt(1), _receipt(2)]
    chain = DashboardQueryAuditChain.from_receipts(receipts)
    verifier = DashboardQueryAuditChainVerifier()

    assert verifier.verify(chain, [receipts[1], receipts[0]]) is False
    assert verifier.verify(chain, [receipts[0]]) is False


def test_audit_chain_rejects_duplicate_ids() -> None:
    receipt = _receipt(1)
    chain = DashboardQueryAuditChain.from_receipts([receipt])

    with pytest.raises(ValueError, match="duplicate"):
        DashboardQueryAuditChainVerifier().verify(chain, [receipt, receipt])
