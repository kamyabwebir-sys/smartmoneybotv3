from smart_money.application.identity_evidence_projection import (
    IdentityEvidenceProjection,
    ingest_identity_evidence,
    project_identity_evidence,
    verify_identity_evidence_replay,
)
from smart_money.domain.chain_identity import IdentityConflict
from smart_money.domain.identity_evidence import IdentityEvidence, IdentityEvidenceStatus
from smart_money.ingestion.ledger import EvidenceGroundingLedger


def _evidence(status=IdentityEvidenceStatus.CONFIRMED, conflict=None):
    return IdentityEvidence(
        subject="evm:base:0xabc",
        subject_kind="wallet",
        status=status,
        source_id="gmgn",
        provenance={"source_revision": "r1", "observed_at": "1700000000"},
        conflict=conflict,
    )


def test_projection_preserves_status_provenance_and_is_deterministic():
    left = project_identity_evidence(_evidence(), timestamp=1_700_000_000)
    right = IdentityEvidenceProjection.from_identity_evidence(
        _evidence(), timestamp=1_700_000_000
    )
    assert left.payload == right.payload
    assert left.evidence_id == left.payload.get_canonical_id()
    assert left.payload.metadata["verification_status"] == "CONFIRMED"
    assert left.payload.metadata["provenance"]["source_revision"] == "r1"
    assert left.payload.data["identity_evidence"]["status"] == "CONFIRMED"


def test_conflict_evidence_is_retained_without_truth_promotion():
    conflict = IdentityConflict("chain_mismatch", "evm:base:a", "evm:bsc:a")
    projected = project_identity_evidence(
        _evidence(IdentityEvidenceStatus.CONFLICT, conflict), timestamp=10
    )
    assert projected.payload.metadata["classification"] == "EVIDENCE"
    assert projected.payload.metadata["verification_status"] == "CONFLICT"
    assert projected.payload.data["identity_evidence"]["conflict"]["code"] == (
        "chain_mismatch"
    )


def test_ingestion_is_idempotent_and_replayable():
    ledger = EvidenceGroundingLedger()
    evidence = _evidence()
    first = ingest_identity_evidence(evidence, ledger, timestamp=10)
    second = ingest_identity_evidence(evidence, ledger, timestamp=10)
    assert first.evidence_id == second.evidence_id
    assert first.receipt_id != second.receipt_id
    assert first.already_present is False
    assert second.already_present is True
    assert ledger.entry_count == 1
    retained = ledger.get(first.evidence_id)
    assert retained is not None
    assert retained == project_identity_evidence(evidence, timestamp=10).payload


def test_timestamp_is_explicit():
    try:
        project_identity_evidence(_evidence(), timestamp=True)
    except TypeError as exc:
        assert "timestamp" in str(exc)
    else:
        raise AssertionError("boolean timestamp must fail closed")


def test_replay_verifier_matches_persisted_projection():
    ledger = EvidenceGroundingLedger()
    evidence = _evidence()
    ingest_identity_evidence(evidence, ledger, timestamp=10)
    receipt = verify_identity_evidence_replay(evidence, ledger, timestamp=10)
    assert receipt.evidence_id == project_identity_evidence(
        evidence, timestamp=10
    ).evidence_id
    assert receipt.identity_evidence_id == evidence.evidence_id


def test_replay_verifier_fails_on_projection_drift():
    ledger = EvidenceGroundingLedger()
    evidence = _evidence()
    ingest_identity_evidence(evidence, ledger, timestamp=10)
    try:
        verify_identity_evidence_replay(evidence, ledger, timestamp=11)
    except ValueError as exc:
        assert "missing" in str(exc) or "match" in str(exc)
    else:
        raise AssertionError("timestamp drift must fail closed")
