import pytest

from smart_money.application.dashboard_audit_head_anchor import (
    DashboardAuditHeadAnchor,
)
from smart_money.application.dashboard_query_audit_chain import (
    DashboardQueryAuditChain,
)
from smart_money.application.dashboard_query_replay_verifier import (
    DashboardQueryReplayReceipt,
)


def _chain(count: int = 2) -> DashboardQueryAuditChain:
    return DashboardQueryAuditChain.from_receipts(
        [
            DashboardQueryReplayReceipt(
                query_id=f"q-{index}",
                expected_receipt_id=f"e-{index}",
                actual_receipt_id=f"a-{index}",
                matches=True,
            )
            for index in range(count)
        ]
    )


def test_head_anchor_matches_chain_deterministically() -> None:
    chain = _chain()
    anchor = DashboardAuditHeadAnchor.from_chain(chain)

    assert anchor.matches(chain) is True
    assert anchor.receipt_count == 2
    assert anchor.latest_verification_id == chain.receipts[-1].verification_id
    assert anchor.anchor_id == DashboardAuditHeadAnchor.from_chain(chain).anchor_id


def test_head_anchor_rejects_forked_chain() -> None:
    anchor = DashboardAuditHeadAnchor.from_chain(_chain())

    assert anchor.matches(_chain(1)) is False


def test_head_anchor_rejects_invalid_count() -> None:
    with pytest.raises(ValueError, match="receipt_count"):
        DashboardAuditHeadAnchor(
            chain_id="chain",
            chain_hash="a" * 64,
            receipt_count=-1,
            latest_verification_id=None,
        )
