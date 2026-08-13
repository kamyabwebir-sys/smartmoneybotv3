from smart_money.ingestion.contracts import EvidencePayload
from smart_money.ingestion.ledger import EvidenceGroundingLedger
from smart_money.ingestion.provider import EvidenceIngestionProvider


def test_ledger_records_accepted_evidence():
    ledger = EvidenceGroundingLedger()
    provider = EvidenceIngestionProvider(ledger=ledger)  # No registry for this test

    payload = EvidencePayload(
        source_id="SRC_001",
        evidence_type="market_structure",
        timestamp=1625097600,
        data={"trend": "bullish"},
    )

    result = provider.ingest(payload)

    assert result.accepted is True
    assert ledger.count() == 1
    assert ledger.get_all()[0]["canonical_id"] == result.canonical_id
    assert ledger.get_all()[0]["data"]["trend"] == "bullish"


def test_ledger_does_not_record_duplicates():
    ledger = EvidenceGroundingLedger()
    provider = EvidenceIngestionProvider(ledger=ledger)

    payload = EvidencePayload(
        source_id="S1", evidence_type="T1", timestamp=100, data={}
    )

    provider.ingest(payload)  # First time
    provider.ingest(payload)  # Duplicate

    assert ledger.count() == 1
