import pytest

from smart_money.domain.chain_identity import IdentityConflict
from smart_money.domain.identity_evidence import (
    IdentityEvidence,
    IdentityEvidenceStatus,
)
from smart_money.reporting.identity_conflict_report import (
    render_identity_conflict_report,
)


def _evidence(status=IdentityEvidenceStatus.CONFLICT):
    return IdentityEvidence(
        subject="evm:base:0xabc",
        subject_kind="wallet",
        status=status,
        source_id="provider-a",
        provenance={"event": "evt-1", "method": "dual-read"},
        conflict=(
            IdentityConflict("chain_mismatch", "evm:base:x", "evm:bsc:x")
            if status is IdentityEvidenceStatus.CONFLICT
            else None
        ),
    )


def test_conflict_report_preserves_evidence_without_truth_promotion():
    report = render_identity_conflict_report(_evidence())
    assert report.conflict_code == "chain_mismatch"
    assert report.left == "evm:base:x"
    assert report.right == "evm:bsc:x"
    assert report.evidence_id == _evidence().evidence_id
    assert report.provenance["method"] == "dual-read"
    assert report.report_id == render_identity_conflict_report(_evidence()).report_id


def test_non_conflict_cannot_render_as_conflict_report():
    with pytest.raises(ValueError, match="CONFLICT"):
        render_identity_conflict_report(_evidence(IdentityEvidenceStatus.UNKNOWN))
