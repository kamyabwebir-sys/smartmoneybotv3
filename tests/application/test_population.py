from types import MappingProxyType

import pytest

from contracts import EvidencePayload
from ledger import EvidenceGroundingLedger
from smart_money.application.population import (
    EvidencePopulator as CanonicalEvidencePopulator,
)


def test_full_flow_ingest_to_population():
    ledger = EvidenceGroundingLedger()
    populator = CanonicalEvidencePopulator()

    # Simulate an entry in ledger
    payload = EvidencePayload("S1", "market_structure", 100, {"trend": "bullish"})
    ledger.record(payload)

    # Process from ledger to domain
    entries = list(ledger.get_unprocessed_entries())
    assert len(entries) == 1

    domain_obj = populator.populate(entries[0])
    assert domain_obj["id"] == entries[0].canonical_id
    assert domain_obj["raw_data"]["trend"] == "bullish"


def test_projection_is_deeply_immutable():
    ledger = EvidenceGroundingLedger()
    payload = EvidencePayload(
        "S1",
        "market_structure",
        100,
        {"levels": [100, 101], "context": {"trend": "bullish"}},
    )
    ledger.record(payload)
    entry = next(ledger.get_all_entries())

    populator = CanonicalEvidencePopulator()
    projection = populator.populate(entry)

    assert isinstance(projection, MappingProxyType)
    assert isinstance(projection["raw_data"], MappingProxyType)
    assert projection["raw_data"]["levels"] == (100, 101)
    assert populator.domain_evidences == (projection,)

    with pytest.raises(TypeError):
        projection["type"] = "changed"

    with pytest.raises(TypeError):
        projection["raw_data"]["context"]["trend"] = "changed"
