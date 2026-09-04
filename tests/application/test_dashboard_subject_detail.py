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
from smart_money.application.dashboard_subject_detail import (
    DashboardSubjectDetail,
)
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)
from smart_money.reporting.macro_markdown_report import (
    render_persian_macro_markdown,
)


def _response(tmp_path, subject_id="evm:base:token-1"):
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
        MacroContextBinding.for_token(subject_id, context)
    )
    report = render_persian_macro_markdown(model)
    snapshot = JsonMacroReportSnapshotStore().save(
        report,
        tmp_path / "macro-report.json",
    )
    return DashboardMacroReadResponse.from_report(report, snapshot)


def test_detail_is_canonical_and_replay_stable(tmp_path) -> None:
    response = _response(tmp_path)
    detail = DashboardSubjectDetail.from_response(response)

    assert detail.subject_id == "evm:base:token-1"
    assert detail.subject_kind == "TOKEN"
    assert detail.context_status == "PROVISIONAL"
    assert detail.observation_count == 1
    assert detail.detail_id == DashboardSubjectDetail.from_response(
        response,
    ).detail_id
    assert detail.canonical_dict()["response_id"] == response.response_id


def test_detail_rejects_malformed_canonical_report() -> None:
    class Response:
        subject_id = "evm:base:token-1"
        response_id = "response"
        markdown = "# no canonical fields"

    with pytest.raises(TypeError):
        DashboardSubjectDetail.from_response(Response())
