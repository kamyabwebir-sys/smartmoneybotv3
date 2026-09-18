import pytest

from smart_money.adapters.persistence.identity_audit_snapshot_store import (
    IdentityAuditSnapshot,
    JsonIdentityAuditSnapshotStore,
)
from smart_money.domain.chain_identity import IdentityConflict
from smart_money.domain.identity_evidence import (
    IdentityEvidence,
    IdentityEvidenceStatus,
)


def _evidence():
    return IdentityEvidence(
        subject="evm:base:0xabc",
        subject_kind="wallet",
        status=IdentityEvidenceStatus.CONFLICT,
        source_id="provider-a",
        provenance={"event": "evt-1"},
        conflict=IdentityConflict("chain_mismatch", "evm:base:x", "evm:bsc:x"),
    )


def test_snapshot_round_trip_and_replay(tmp_path):
    path = tmp_path / "identity-audit.json"
    store = JsonIdentityAuditSnapshotStore()
    evidence = _evidence()
    saved = store.save(evidence, path)
    loaded = store.load(path)
    assert loaded == saved
    receipt = store.replay(evidence, loaded)
    assert receipt.matches is True
    assert receipt.evidence_id == evidence.evidence_id


def test_snapshot_rejects_tampered_content(tmp_path):
    path = tmp_path / "identity-audit.json"
    store = JsonIdentityAuditSnapshotStore()
    store.save(_evidence(), path)
    document = path.read_text(encoding="utf-8").replace("chain_mismatch", "address_collision")
    path.write_text(document, encoding="utf-8")
    with pytest.raises(ValueError, match="hash|canonical"):
        store.load(path)


def test_snapshot_is_immutable_contract():
    assert IdentityAuditSnapshot.__dataclass_params__.frozen is True
