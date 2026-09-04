from decimal import Decimal

import pytest

from smart_money.analytics.macro_context_projection import (
    MacroAnalyticsContext,
    MacroContextStatus,
)
from smart_money.application.macro_window_query import MacroEvidenceWindow
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)


def _observation(
    observed_at: int,
    status: MacroObservationStatus,
) -> MacroEvidenceObservation:
    return MacroEvidenceObservation(
        source_id="worldmonitor",
        metric="risk_sentiment",
        observed_at=observed_at,
        value=Decimal(str(observed_at)),
        unit="index",
        status=status,
        source_revision=f"r{observed_at}",
    )


def _window(
    observations: tuple[MacroEvidenceObservation, ...],
    conflicted_count: int = 0,
    unknown_count: int = 0,
) -> MacroEvidenceWindow:
    return MacroEvidenceWindow(
        metric="risk_sentiment",
        start_at=0,
        end_at=100,
        observations=observations,
        conflicted_count=conflicted_count,
        unknown_count=unknown_count,
    )


def test_context_selects_latest_observation_without_scoring() -> None:
    context = MacroAnalyticsContext.from_window(
        _window(
            (
                _observation(10, MacroObservationStatus.PROVISIONAL),
                _observation(20, MacroObservationStatus.CONFIRMED),
            )
        )
    )

    assert context.latest_observation is not None
    assert context.latest_observation.observed_at == 20
    assert context.status is MacroContextStatus.CONFIRMED
    assert context.observation_count == 2
    assert context.canonical_id == MacroAnalyticsContext.from_window(
        _window(
            (
                _observation(10, MacroObservationStatus.PROVISIONAL),
                _observation(20, MacroObservationStatus.CONFIRMED),
            )
        )
    ).canonical_id


@pytest.mark.parametrize(
    ("window", "expected"),
    [
        (_window(()), MacroContextStatus.MISSING),
        (
            _window(
                (_observation(10, MacroObservationStatus.CONFIRMED),),
                conflicted_count=1,
            ),
            MacroContextStatus.CONFLICTED,
        ),
        (
            _window(
                (_observation(10, MacroObservationStatus.UNKNOWN),),
                unknown_count=1,
            ),
            MacroContextStatus.UNKNOWN,
        ),
    ],
)
def test_context_is_conservative_about_missing_and_conflicts(
    window: MacroEvidenceWindow,
    expected: MacroContextStatus,
) -> None:
    assert MacroAnalyticsContext.from_window(window).status is expected


def test_context_rejects_inconsistent_cardinality() -> None:
    with pytest.raises(ValueError, match="latest observation"):
        MacroAnalyticsContext(
            metric="risk_sentiment",
            start_at=0,
            end_at=1,
            latest_observation=None,
            status=MacroContextStatus.CONFIRMED,
            observation_count=1,
            conflicted_count=0,
            unknown_count=0,
        )
