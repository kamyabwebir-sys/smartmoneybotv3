from smart_money.adapters.persistence.identity_evidence_store import JsonIdentityEvidenceStore
from smart_money.application.identity_evidence_projection import (
    project_identity_evidence,
)
from smart_money.domain.identity_evidence import (
    IdentityEvidence,
    IdentityEvidenceStatus,
)


def _payload():
    return project_identity_evidence(
        IdentityEvidence(
            subject="evm:base:0xabc",
            subject_kind="wallet",
            status=IdentityEvidenceStatus.CONFIRMED,
            source_id="gmgn",
            provenance={"revision": "r1"},
        ),
        timestamp=10,
    ).payload


def test_store_round_trips_payload_and_is_idempotent(tmp_path):
    path = tmp_path / "identity.json"
    payload = _payload()
    first = JsonIdentityEvidenceStore(path)
    identity = first.append(payload)
    assert first.append(payload) == identity
    assert first.entry_count == 1
    second = JsonIdentityEvidenceStore(path)
    assert second.get(identity) == payload
    assert list(second.iter_payloads()) == [payload]
    assert second.content_hash == first.content_hash


def test_store_rejects_non_identity_payload(tmp_path):
    path = tmp_path / "identity.json"
    from smart_money.ingestion.contracts import EvidencePayload
    other = EvidencePayload("x", "generic", 1, {"x": 1})
    store = JsonIdentityEvidenceStore(path)
    try:
        store.append(other)
    except ValueError as exc:
        assert "identity" in str(exc)
    else:
        raise AssertionError("non-identity payload must fail closed")
