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
from smart_money.reporting.macro_markdown_report import (
    render_persian_macro_markdown,
)


def _model(
    status: MacroContextStatus = MacroContextStatus.PROVISIONAL,
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


def test_markdown_report_contains_persian_sections_and_provenance() -> None:
    report = render_persian_macro_markdown(_model())

    assert report.markdown.startswith("# گزارش فارسی وضعیت کلان\n")
    assert "## خلاصه" in report.markdown
    assert "## آخرین مشاهده" in report.markdown
    assert "## منشأ داده" in report.markdown
    assert "worldmonitor" in report.markdown
    assert "توصیهٔ خرید، فروش یا محاسبهٔ ریسک نیست" in report.markdown
    assert report.report_id == render_persian_macro_markdown(_model()).report_id


@pytest.mark.parametrize(
    ("status", "missing", "expected"),
    [
        (MacroContextStatus.MISSING, True, "دادهٔ کلان معتبری"),
        (MacroContextStatus.CONFLICTED, False, "تضاد"),
    ],
)
def test_markdown_report_exposes_missing_or_conflict(
    status: MacroContextStatus,
    missing: bool,
    expected: str,
) -> None:
    report = render_persian_macro_markdown(_model(status, missing=missing))

    assert expected in report.markdown
    assert "MACRO_CONTEXT_" in report.markdown


def test_markdown_report_escapes_table_cells() -> None:
    model = _model()
    report = render_persian_macro_markdown(model)

    assert "| شاخص | وضعیت | زمان مشاهده | مقدار | واحد |" in report.markdown


def test_markdown_report_rejects_non_read_model() -> None:
    with pytest.raises(TypeError, match="MacroContextReadModel"):
        render_persian_macro_markdown(object())  # type: ignore[arg-type]
