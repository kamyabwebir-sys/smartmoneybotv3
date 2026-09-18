from decimal import Decimal

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
from smart_money.application.dashboard_macro_read_index import (
    DashboardMacroReadIndex,
)
from smart_money.application.dashboard_query_audit_receipt import (
    DashboardQueryAuditReceipt,
)
from smart_money.application.dashboard_query_endpoint import (
    DashboardQueryEndpoint,
)
from smart_money.application.dashboard_query_error import DashboardQueryError
from smart_money.application.dashboard_query_result import (
    DashboardQueryResultStatus,
)
from smart_money.application.dashboard_subject_detail_query import (
    DashboardSubjectDetailQuery,
)
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)
from smart_money.reporting.macro_markdown_report import (
    render_persian_macro_markdown,
)


def _response(tmp_path, subject_id: str) -> DashboardMacroReadResponse:
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


def test_endpoint_returns_canonical_result(tmp_path) -> None:
    response = _response(tmp_path, "evm:base:token-endpoint")
    endpoint = DashboardQueryEndpoint(
        DashboardMacroReadIndex.from_responses([response])
    )
    query = DashboardSubjectDetailQuery(query="token-endpoint")

    result = endpoint.execute(query)

    assert result.status is DashboardQueryResultStatus.SUCCESS
    assert result.query.query_id == query.query_id
    assert result.page.items[0].subject_id == response.subject_id


def test_endpoint_returns_empty_result(tmp_path) -> None:
    endpoint = DashboardQueryEndpoint(DashboardMacroReadIndex.from_responses([]))

    result = endpoint.execute(DashboardSubjectDetailQuery(query="missing"))

    assert result.status is DashboardQueryResultStatus.EMPTY
    assert result.page.items == ()


def test_endpoint_safe_returns_canonical_error_for_invalid_query(tmp_path) -> None:
    endpoint = DashboardQueryEndpoint(DashboardMacroReadIndex.from_responses([]))

    error = endpoint.execute_safe(object())

    assert isinstance(error, DashboardQueryError)
    assert error.error_code == "INVALID_QUERY"
    assert error.query_id is None
    assert error.error_id == endpoint.execute_safe(object()).error_id


def test_endpoint_safe_preserves_empty_subject_result(tmp_path) -> None:
    response = _response(tmp_path, "evm:base:token-error")
    endpoint = DashboardQueryEndpoint(
        DashboardMacroReadIndex.from_responses([response])
    )
    query = DashboardSubjectDetailQuery(query="missing")

    result = endpoint.execute_safe(query)

    assert result.status is DashboardQueryResultStatus.EMPTY
    assert result.query.query_id == query.query_id


def test_endpoint_emits_deterministic_audit_receipt(tmp_path) -> None:
    response = _response(tmp_path, "evm:base:token-receipt")
    endpoint = DashboardQueryEndpoint(
        DashboardMacroReadIndex.from_responses([response])
    )
    query = DashboardSubjectDetailQuery(query="receipt")

    outcome, receipt = endpoint.execute_with_receipt(query)

    assert isinstance(receipt, DashboardQueryAuditReceipt)
    assert receipt.status == "SUCCESS"
    assert receipt.artifact_kind == "result"
    assert receipt.query_id == query.query_id
    assert len(receipt.output_hash) == 64
    assert receipt.receipt_id == endpoint.execute_with_receipt(query)[1].receipt_id
    assert outcome.page.items[0].subject_id == response.subject_id


def test_endpoint_emits_error_audit_receipt() -> None:
    endpoint = DashboardQueryEndpoint(DashboardMacroReadIndex.from_responses([]))

    outcome, receipt = endpoint.execute_with_receipt(object())

    assert isinstance(outcome, DashboardQueryError)
    assert receipt.status == "ERROR"
    assert receipt.artifact_kind == "error"
    assert receipt.error_code == "INVALID_QUERY"
    assert receipt.query_id is None
