import pytest

from smart_money.adapters.persistence.identity_audit_snapshot_store import (
    IdentityAuditSnapshot,
)
from smart_money.application.identity_snapshot_ledger_binding import (
    bind_identity_snapshot_to_ledger,
)
from smart_money.domain.identity_evidence import (
    IdentityEvidence,
    IdentityEvidenceStatus,
)
from smart_money.ingestion.ledger import EvidenceGroundingLedger


def _evidence():
    return IdentityEvidence(
        subject="evm:base:0xabc",
        subject_kind="wallet",
        status=IdentityEvidenceStatus.CONFIRMED,
        source_id="provider-a",
        provenance={"event": "evt-1"},
    )


def test_snapshot_binding_appends_and_is_idempotent(tmp_path):
    evidence = _evidence()
    snapshot = IdentityAuditSnapshot.from_evidence(evidence)
    ledger = EvidenceGroundingLedger()
    first = bind_identity_snapshot_to_ledger(
        snapshot, evidence, ledger, timestamp=10
    )
    second = bind_identity_snapshot_to_ledger(
        snapshot, evidence, ledger, timestamp=10
    )
    assert first.snapshot_evidence_id == evidence.evidence_id
    assert first.ledger_evidence_id == second.ledger_evidence_id
    assert first.already_present is False
    assert second.already_present is True
    assert ledger.entry_count == 1


def test_binding_rejects_snapshot_drift():
    evidence = _evidence()
    other = IdentityEvidence(
        subject="evm:base:0xdef",
        subject_kind="wallet",
        status=IdentityEvidenceStatus.CONFIRMED,
        source_id="provider-a",
        provenance={"event": "evt-2"},
    )
    drifted = IdentityAuditSnapshot.from_evidence(other)
    with pytest.raises(ValueError, match="does not match"):
        bind_identity_snapshot_to_ledger(
            drifted, evidence, EvidenceGroundingLedger(), timestamp=10
        )


def test_binding_requires_explicit_integer_timestamp():
    evidence = _evidence()
    snapshot = IdentityAuditSnapshot.from_evidence(evidence)
    with pytest.raises(TypeError, match="timestamp"):
        bind_identity_snapshot_to_ledger(
            snapshot, evidence, EvidenceGroundingLedger(), timestamp=True
        )
