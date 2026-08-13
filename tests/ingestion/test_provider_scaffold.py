import pytest

from smart_money.ingestion.contracts import EvidencePayload
from smart_money.ingestion.errors import InvalidPayloadError
from smart_money.ingestion.provider import EvidenceIngestionProvider


def test_deterministic_ingestion():
    provider = EvidenceIngestionProvider()
    payload = EvidencePayload(
        source_id="test-source", timestamp=1000, data={"price": 100.5}
    )

    res1 = provider.ingest(payload)
    assert res1.accepted is True

    # Idempotency: Second ingestion of same payload
    res2 = provider.ingest(payload)
    assert res2.accepted is False
    assert res2.canonical_id == res1.canonical_id


def test_fail_closed_on_invalid_input():
    provider = EvidenceIngestionProvider()
    bad_payload = EvidencePayload(source_id="", timestamp=0, data={})

    with pytest.raises(InvalidPayloadError):
        provider.ingest(bad_payload)


def test_replayability_across_instances():
    payload = EvidencePayload(source_id="S1", timestamp=123, data={"v": 1})

    # Identical inputs must yield identical canonical IDs
    id1 = payload.get_canonical_id()
    id2 = payload.get_canonical_id()
    assert id1 == id2
