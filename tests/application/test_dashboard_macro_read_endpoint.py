from decimal import Decimal

import pytest

from smart_money.adapters.persistence.macro_report_snapshot_store import (
    JsonMacroReportSnapshotStore,
)
from smart_money.analytics.macro_context_binding import MacroContextBinding
from smart_money.analytics.macro_context_projection import (
    MacroAnalyticsContext,
    MacroContextStatus,
)
from smart_money.analytics.macro_context_read_model import MacroContextReadModel
from smart_money.application.dashboard_macro_read_endpoint import (
    DashboardMacroReadResponse,
)
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)
from smart_money.reporting.macro_markdown_report import (
    render_persian_macro_markdown,
)


def _report():
    observation = MacroEvidenceObservation(
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
        latest_observation=observation,
        status=MacroContextStatus.PROVISIONAL,
        observation_count=1,
        conflicted_count=0,
        unknown_count=0,
    )
    model = MacroContextReadModel.from_binding(
        MacroContextBinding.for_token("evm:base:token-1", context)
    )
    return render_persian_macro_markdown(model)


def test_dashboard_response_is_read_only_and_canonical(tmp_path) -> None:
    report = _report()
    snapshot = JsonMacroReportSnapshotStore().save(
        report,
        tmp_path / "macro-report.json",
    )
    response = DashboardMacroReadResponse.from_report(report, snapshot)

    assert response.report_id == report.report_id
    assert response.subject_id == "evm:base:token-1"
    assert response.snapshot_content_hash == snapshot.content_hash
    assert response.response_id == DashboardMacroReadResponse.from_report(
        report,
        snapshot,
    ).response_id
    assert "توصیهٔ خرید، فروش" in response.markdown


def test_dashboard_response_rejects_snapshot_drift(tmp_path) -> None:
    report = _report()
    snapshot = JsonMacroReportSnapshotStore().save(
        report,
        tmp_path / "macro-report.json",
    )
    class DriftedSnapshot:
        report_id = snapshot.report_id
        model_id = snapshot.model_id
        explanation_id = snapshot.explanation_id
        subject_id = snapshot.subject_id
        markdown = snapshot.markdown + "\n"
        content_hash = snapshot.content_hash

    drifted = DriftedSnapshot()

    with pytest.raises(ValueError, match="markdown"):
        DashboardMacroReadResponse.from_report(report, drifted)


def test_dashboard_response_rejects_non_snapshot() -> None:
    with pytest.raises(TypeError, match="snapshot"):
        DashboardMacroReadResponse.from_report(_report(), object())
