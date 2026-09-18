from decimal import Decimal

import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.macro_ledger_ingestion import (
    ingest_macro_evidence,
)
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)


def _observation() -> MacroEvidenceObservation:
    return MacroEvidenceObservation(
        source_id="worldmonitor",
        metric="risk_sentiment",
        observed_at=1_700_000_000,
        value=Decimal("0.25"),
        unit="index",
        status=MacroObservationStatus.PROVISIONAL,
        source_revision="r1",
    )


def test_macro_evidence_is_appended_idempotently() -> None:
    ledger = EvidenceGroundingLedger()

    first = ingest_macro_evidence(_observation(), ledger)
    second = ingest_macro_evidence(_observation(), ledger)

    assert first.already_present is False
    assert second.already_present is True
    assert first.evidence_id == second.evidence_id
    assert first.observation_id == second.observation_id
    assert first.ledger_entry_count == second.ledger_entry_count == 1
    assert ledger.entry_count == 1


def test_receipt_is_deterministic_and_external_status_is_retained() -> None:
    ledger = EvidenceGroundingLedger()
    receipt = ingest_macro_evidence(_observation(), ledger)
    payload = ledger.get(receipt.evidence_id)

    assert receipt.receipt_id == (
        ingest_macro_evidence(_observation(), ledger).receipt_id
    )
    assert payload is not None
    assert payload.metadata["authority"] == "EXTERNAL_NON_AUTHORITATIVE"
    assert payload.metadata["verification_status"] == "PROVISIONAL"


class _MismatchedLedger:
    def __init__(self) -> None:
        self._ledger = EvidenceGroundingLedger()

    def append(self, payload):
        self._ledger.append(payload)
        return "wrong-id"

    def contains(self, canonical_id):
        return self._ledger.contains(canonical_id)

    def get(self, canonical_id):
        return self._ledger.get(canonical_id)

    def iter_payloads(self):
        return self._ledger.iter_payloads()

    @property
    def entry_count(self):
        return self._ledger.entry_count


def test_ingestion_fails_closed_on_mismatched_ledger_identity() -> None:
    with pytest.raises(ValueError, match="mismatched evidence identity"):
        ingest_macro_evidence(_observation(), _MismatchedLedger())
