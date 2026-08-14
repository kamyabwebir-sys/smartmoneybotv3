from contracts import EvidencePayload
from ledger import EvidenceGroundingLedger
from smart_money.ingestion.provider import (
    EvidenceIngestionProvider as CanonicalEvidenceIngestionProvider,
)


def test_ledger_grounding_on_ingest():
    ledger = EvidenceGroundingLedger()
    provider = CanonicalEvidenceIngestionProvider(ledger=ledger)

    payload = EvidencePayload("S1", "market_structure", 100, {"price": 50000})
    result = provider.ingest(payload)

    assert result.accepted is True
    assert ledger.count == 1

    grounded = ledger.get_entry(result.canonical_id)
    assert grounded is not None
    assert grounded.payload.data["price"] == 50000


def test_no_grounding_on_duplicate():
    ledger = EvidenceGroundingLedger()
    provider = CanonicalEvidenceIngestionProvider(ledger=ledger)

    payload = EvidencePayload("S1", "market_structure", 100, {"price": 50000})
    first = provider.ingest(payload)
    assert ledger.count == 1

    # Ingest same again
    duplicate = provider.ingest(payload)
    assert ledger.count == 1  # Should not increase
    assert first.accepted is True
    assert duplicate.accepted is False
    assert duplicate.canonical_id == first.canonical_id
