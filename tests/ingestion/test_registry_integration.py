import pytest
from smart_money.ingestion.provider import EvidenceIngestionProvider
from smart_money.ingestion.contracts import EvidencePayload


class MockRegistry:
    def __init__(self, supported_types):
        self._registry = {t: True for t in supported_types}


def test_rejects_unregistered_evidence_type():
    registry = MockRegistry(supported_types=["valid_type"])
    provider = EvidenceIngestionProvider(registry=registry)

    payload = EvidencePayload(
        source_id="S1", evidence_type="invalid_type", timestamp=1000, data={}
    )

    result = provider.ingest(payload)
    assert result.accepted is False
    assert "Unsupported evidence type" in result.message


def test_accepts_registered_evidence_type():
    registry = MockRegistry(supported_types=["valid_type"])
    provider = EvidenceIngestionProvider(registry=registry)

    payload = EvidencePayload(
        source_id="S1", evidence_type="valid_type", timestamp=1000, data={}
    )

    result = provider.ingest(payload)
    assert result.accepted is True
