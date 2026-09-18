from decimal import Decimal

import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.macro_ledger_ingestion import ingest_macro_evidence
from smart_money.application.macro_window_query import (
    query_macro_evidence_window,
)
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)


def _observation(
    observed_at: int,
    *,
    metric: str = "risk_sentiment",
    status: MacroObservationStatus = MacroObservationStatus.PROVISIONAL,
) -> MacroEvidenceObservation:
    return MacroEvidenceObservation(
        source_id="worldmonitor",
        metric=metric,
        observed_at=observed_at,
        value=Decimal(str(observed_at)),
        unit="index",
        status=status,
        source_revision=f"r{observed_at}",
    )


def test_window_query_is_bounded_sorted_and_reports_statuses() -> None:
    ledger = EvidenceGroundingLedger()
    for observation in (
        _observation(30, status=MacroObservationStatus.UNKNOWN),
        _observation(10),
        _observation(20, status=MacroObservationStatus.CONFLICTED),
        _observation(100, metric="inflation"),
    ):
        ingest_macro_evidence(observation, ledger)

    result = query_macro_evidence_window(
        ledger,
        metric="risk_sentiment",
        start_at=10,
        end_at=30,
    )

    assert [item.observed_at for item in result.observations] == [10, 20, 30]
    assert result.matched_count == 3
    assert result.conflicted_count == 1
    assert result.unknown_count == 1
    assert result.missing is False


def test_window_query_is_idempotent_and_reports_missing() -> None:
    ledger = EvidenceGroundingLedger()
    observation = _observation(10)
    ingest_macro_evidence(observation, ledger)
    ingest_macro_evidence(observation, ledger)

    result = query_macro_evidence_window(
        ledger,
        metric="does_not_exist",
        start_at=0,
        end_at=100,
    )

    assert result.observations == ()
    assert result.matched_count == 0
    assert result.missing is True


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"metric": "", "start_at": 0, "end_at": 1}, "metric"),
        ({"metric": "x", "start_at": 2, "end_at": 1}, "start_at"),
        ({"metric": "x", "start_at": -1, "end_at": 1}, "bounds"),
    ],
)
def test_window_query_rejects_invalid_bounds(kwargs: dict[str, object], error: str) -> None:
    with pytest.raises((TypeError, ValueError), match=error):
        query_macro_evidence_window(
            EvidenceGroundingLedger(),
            **kwargs,
        )
