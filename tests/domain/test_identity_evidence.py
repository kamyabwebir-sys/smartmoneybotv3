from dataclasses import FrozenInstanceError

import pytest

from smart_money.domain.chain_identity import IdentityConflict
from smart_money.domain.identity_evidence import (
    IdentityEvidence,
    IdentityEvidenceStatus,
)


def test_identity_evidence_is_canonical_replayable_and_not_truth() -> None:
    evidence = IdentityEvidence(
        subject="evm:base:0xabc",
        subject_kind="wallet",
        status=IdentityEvidenceStatus.CONFIRMED,
        source_id="provider-a",
        provenance={"source_event_id": "event-1", "method": "canonical"},
    )
    assert evidence.evidence_id == IdentityEvidence(
        subject="evm:base:0xabc",
        subject_kind="wallet",
        status=IdentityEvidenceStatus.CONFIRMED,
        source_id="provider-a",
        provenance={"method": "canonical", "source_event_id": "event-1"},
    ).evidence_id
    with pytest.raises(FrozenInstanceError):
        evidence.status = IdentityEvidenceStatus.UNKNOWN  # type: ignore[misc]


def test_conflict_status_requires_explicit_conflict() -> None:
    conflict = IdentityConflict("chain_mismatch", "evm:base:x", "solana:mainnet-beta:x")
    evidence = IdentityEvidence(
        subject="legacy-wallet",
        subject_kind="wallet",
        status=IdentityEvidenceStatus.CONFLICT,
        source_id="provider-a",
        provenance={"source_event_id": "event-2"},
        conflict=conflict,
    )
    assert evidence.canonical_dict()["status"] == "CONFLICT"
    with pytest.raises(ValueError, match="requires conflict"):
        IdentityEvidence(
            subject="x",
            subject_kind="wallet",
            status=IdentityEvidenceStatus.CONFLICT,
            source_id="s",
            provenance={"event": "1"},
        )
