import pytest
from provider import EvidenceIngestionProvider
from ledger import EvidenceGroundingLedger
from contracts import EvidencePayload


def test_ledger_grounding_on_ingest():
    ledger = EvidenceGroundingLedger()
    prov = EvidenceIngestionProvider(ledger=ledger)

    payload = EvidencePayload("S1", "market_structure", 100, {"price": 50000})
    result = prov.ingest(payload)

    assert result.accepted is True
    assert ledger.count == 1

    grounded = ledger.get_entry(result.canonical_id)
    assert grounded is not None
    assert grounded.payload.data["price"] == 50000


def test_no_grounding_on_duplicate():
    ledger = EvidenceGroundingLedger()
    prov = EvidenceIngestionProvider(ledger=ledger)

    payload = EvidencePayload("S1", "market_structure", 100, {"price": 50000})
    prov.ingest(payload)
    assert ledger.count == 1

    # Ingest same again
    prov.ingest(payload)
    assert ledger.count == 1  # Should not increase
