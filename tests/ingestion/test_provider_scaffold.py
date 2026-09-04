import pytest
from smart_money.ingestion.provider import (
    EvidenceIngestionProvider,
    EvidencePayload,
    get_canonical_id,
)


def test_deterministic_ingestion():
    provider = EvidenceIngestionProvider()
    data = {"wallet": "0x1234567890abcdef", "token": "SOL", "amount": 100}
    payload = EvidencePayload(source="test_feed", data=data, observed_slot=1000)

    res1 = provider.ingest(payload)
    assert res1.status == "ACCEPTED"
    assert not res1.is_duplicate
    assert res1.canonical_id == get_canonical_id(data)

    # Idempotent replay test
    res2 = provider.ingest(payload)
    assert res2.status == "IDEMPOTENT_DUPLICATE"
    assert res2.is_duplicate
    assert res2.canonical_id == res1.canonical_id
    assert provider.ledger.count() == 1


def test_fail_closed_on_invalid_input():
    provider = EvidenceIngestionProvider()

    # Invalid source
    with pytest.raises(ValueError, match="source"):
        invalid_payload = EvidencePayload(source="", data={"a": 1})
        provider.ingest(invalid_payload)

    # Empty data
    with pytest.raises(ValueError, match="data"):
        invalid_payload = EvidencePayload(source="feed", data={})
        provider.ingest(invalid_payload)

    # Negative slot
    with pytest.raises(ValueError, match="observed_slot"):
        invalid_payload = EvidencePayload(source="feed", data={"a": 1}, observed_slot=-1)
        provider.ingest(invalid_payload)

    # Invalid type
    with pytest.raises(TypeError):
        provider.ingest("not_a_payload")  # type: ignore


def test_replayability_across_instances():
    data_list = [
        {"item": 1, "value": "A"},
        {"item": 2, "value": "B"},
        {"item": 3, "value": "C"},
    ]

    p1 = EvidenceIngestionProvider()
    p2 = EvidenceIngestionProvider()

    res1 = [p1.ingest(EvidencePayload(source="feed", data=d, observed_slot=10)) for d in data_list]
    res2 = [p2.ingest(EvidencePayload(source="feed", data=d, observed_slot=10)) for d in data_list]

    assert [r.canonical_id for r in res1] == [r.canonical_id for r in res2]
    assert [r.status for r in res1] == [r.status for r in res2]
    assert p1.ledger.get_sequence() == p2.ledger.get_sequence()
