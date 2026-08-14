from collections.abc import Callable, Iterator

import pytest

from smart_money.adapters.persistence.json_ledger import (
    EvidenceGroundingLedger as JsonEvidenceLedger,
)
from smart_money.ingestion.contracts import EvidencePayload
from smart_money.ingestion.ledger import (
    EvidenceGroundingLedger as InMemoryEvidenceLedger,
)
from smart_money.ingestion.ledger import EvidenceLedger
from smart_money.ingestion.provider import EvidenceIngestionProvider

LedgerFactory = Callable[[], EvidenceLedger]


class MismatchedIdentityLedger:
    def append(self, payload: EvidencePayload) -> str:
        return "mismatched-id"

    def contains(self, canonical_id: str) -> bool:
        return False

    def get(self, canonical_id: str) -> EvidencePayload | None:
        return None

    def iter_payloads(self) -> Iterator[EvidencePayload]:
        return iter(())

    @property
    def entry_count(self) -> int:
        return 0


@pytest.fixture(
    params=[InMemoryEvidenceLedger, JsonEvidenceLedger],
    ids=["in-memory", "json"],
)
def ledger(request: pytest.FixtureRequest) -> EvidenceLedger:
    factory: LedgerFactory = request.param
    return factory()


def test_ledger_records_accepted_evidence(ledger: EvidenceLedger):
    provider = EvidenceIngestionProvider(ledger=ledger)  # No registry for this test

    payload = EvidencePayload(
        source_id="SRC_001",
        evidence_type="market_structure",
        timestamp=1625097600,
        data={"trend": "bullish"},
    )

    result = provider.ingest(payload)

    assert result.accepted is True
    assert ledger.entry_count == 1
    assert ledger.get(result.canonical_id) == payload


def test_ledger_does_not_record_duplicates(ledger: EvidenceLedger):
    provider = EvidenceIngestionProvider(ledger=ledger)

    payload = EvidencePayload(
        source_id="S1", evidence_type="T1", timestamp=100, data={}
    )

    provider.ingest(payload)  # First time
    provider.ingest(payload)  # Duplicate

    assert ledger.entry_count == 1


def test_provider_fails_closed_on_mismatched_ledger_identity():
    provider = EvidenceIngestionProvider(ledger=MismatchedIdentityLedger())
    payload = EvidencePayload(
        source_id="S1",
        evidence_type="T1",
        timestamp=100,
        data={},
    )

    with pytest.raises(RuntimeError, match="mismatched canonical identity"):
        provider.ingest(payload)
