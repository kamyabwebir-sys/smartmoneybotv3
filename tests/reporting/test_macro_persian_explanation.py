from decimal import Decimal

import pytest

from smart_money.analytics.macro_context_binding import MacroContextBinding
from smart_money.analytics.macro_context_projection import (
    MacroAnalyticsContext,
    MacroContextStatus,
)
from smart_money.analytics.macro_context_read_model import MacroContextReadModel
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)
from smart_money.reporting.macro_persian_explanation import (
    explain_macro_context,
)


def _model(
    status: MacroContextStatus,
    *,
    missing: bool = False,
) -> MacroContextReadModel:
    latest = None if missing else MacroEvidenceObservation(
        source_id="worldmonitor",
        metric="risk_sentiment",
        observed_at=10,
        value=Decimal("0.25"),
        unit="index",
        status=MacroObservationStatus.PROVISIONAL,
        source_revision="r1",
    )
    context = MacroAnalyticsContext(
        metric="risk_sentiment",
        start_at=0,
        end_at=10,
        latest_observation=latest,
        status=status,
        observation_count=0 if missing else 1,
        conflicted_count=1 if status is MacroContextStatus.CONFLICTED else 0,
        unknown_count=0,
    )
    return MacroContextReadModel.from_binding(
        MacroContextBinding.for_token("evm:base:token-1", context)
    )


def test_explanation_is_persian_and_keeps_non_decision_guardrail() -> None:
    explanation = explain_macro_context(
        _model(MacroContextStatus.PROVISIONAL)
    )

    assert "توکن" in explanation.summary
    assert "worldmonitor" in explanation.provenance
    assert "توصیهٔ خرید یا فروش نیست" in explanation.provenance
    assert explanation.canonical_id == explain_macro_context(
        _model(MacroContextStatus.PROVISIONAL)
    ).canonical_id


@pytest.mark.parametrize(
    ("status", "missing", "expected"),
    [
        (MacroContextStatus.MISSING, True, "دادهٔ کلان معتبری"),
        (MacroContextStatus.CONFLICTED, False, "تضاد"),
    ],
)
def test_explanation_describes_missing_or_conflicted_context(
    status: MacroContextStatus,
    missing: bool,
    expected: str,
) -> None:
    explanation = explain_macro_context(_model(status, missing=missing))
    assert expected in explanation.summary
    assert explanation.status is status


def test_explanation_rejects_non_read_model() -> None:
    with pytest.raises(TypeError, match="MacroContextReadModel"):
        explain_macro_context(object())  # type: ignore[arg-type]
