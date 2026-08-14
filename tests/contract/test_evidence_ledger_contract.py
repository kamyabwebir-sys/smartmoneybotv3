from collections.abc import Callable

import pytest

from smart_money.adapters.persistence.json_ledger import (
    EvidenceGroundingLedger as JsonEvidenceLedger,
)
from smart_money.ingestion.contracts import EvidencePayload
from smart_money.ingestion.ledger import (
    EvidenceGroundingLedger as InMemoryEvidenceLedger,
)
from smart_money.ingestion.ledger import EvidenceLedger

LedgerFactory = Callable[[], EvidenceLedger]


@pytest.fixture(
    params=[InMemoryEvidenceLedger, JsonEvidenceLedger],
    ids=["in-memory", "json"],
)
def ledger(request: pytest.FixtureRequest) -> EvidenceLedger:
    factory: LedgerFactory = request.param
    return factory()


def make_payload(source_id: str, timestamp: int) -> EvidencePayload:
    return EvidencePayload(
        source_id=source_id,
        evidence_type="ledger_contract",
        timestamp=timestamp,
        data={"price": timestamp},
    )


def test_ledger_satisfies_runtime_contract(ledger: EvidenceLedger) -> None:
    assert isinstance(ledger, EvidenceLedger)


def test_append_is_idempotent_and_content_addressed(ledger: EvidenceLedger) -> None:
    payload = make_payload("SRC-1", 100)

    first_id = ledger.append(payload)
    second_id = ledger.append(payload)

    assert first_id == payload.get_canonical_id()
    assert second_id == first_id
    assert ledger.entry_count == 1
    assert ledger.contains(first_id)
    assert ledger.get(first_id) == payload


def test_iteration_preserves_deterministic_insertion_order(
    ledger: EvidenceLedger,
) -> None:
    first = make_payload("SRC-1", 100)
    second = make_payload("SRC-2", 200)

    ledger.append(first)
    ledger.append(second)

    assert tuple(ledger.iter_payloads()) == (first, second)


def test_unknown_identity_returns_none(ledger: EvidenceLedger) -> None:
    assert ledger.get("missing") is None


def test_append_rejects_non_payload(ledger: EvidenceLedger) -> None:
    with pytest.raises(TypeError, match="payload must be an EvidencePayload"):
        ledger.append(object())  # type: ignore[arg-type]
