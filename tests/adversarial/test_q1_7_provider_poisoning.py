from __future__ import annotations

import pytest

from smart_money.ingestion.contracts import EvidencePayload
from smart_money.ingestion.provider import EvidenceIngestionProvider


class PoisonedLedger:
    def contains(self, canonical_id: str) -> bool:
        return False

    def append(self, payload: EvidencePayload) -> str:
        return "forged-canonical-id"


def test_provider_poisoning_mismatched_ledger_identity_fails_closed() -> None:
    provider = EvidenceIngestionProvider(ledger=PoisonedLedger())
    payload = EvidencePayload("poison", "observation", 1, {"value": 1})
    with pytest.raises(RuntimeError, match="mismatched canonical identity"):
        provider.ingest(payload)


def test_provider_rejects_unsupported_type_before_external_append() -> None:
    class Registry:
        def list_ids(self):
            return ("allowed",)

    class CountingLedger:
        def __init__(self):
            self.calls = 0

        def append(self, payload):
            self.calls += 1
            return payload.get_canonical_id()

        def contains(self, canonical_id):
            return False

    ledger = CountingLedger()
    provider = EvidenceIngestionProvider(registry=Registry(), ledger=ledger)
    result = provider.ingest(EvidencePayload("poison", "blocked", 1, {"x": 1}))
    assert result.accepted is False
    assert ledger.calls == 0
