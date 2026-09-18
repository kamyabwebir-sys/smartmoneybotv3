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
from smart_money.application.dashboard_macro_read_index import (
    DashboardMacroReadIndex,
)
from smart_money.application.dashboard_query_result import (
    DashboardQueryResult,
    DashboardQueryResultStatus,
)
from smart_money.application.dashboard_subject_detail import (
    DashboardSubjectDetail,
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


def _response(
    subject_id: str,
    tmp_path,
    kind: str = "TOKEN",
    observed_at: int = 10,
) -> DashboardMacroReadResponse:
    observation = MacroEvidenceObservation(
        source_id="worldmonitor",
        metric="risk_sentiment",
        observed_at=observed_at,
        value=Decimal("0.25"),
        unit="index",
        status=MacroObservationStatus.PROVISIONAL,
        source_revision="r1",
    )
    context = MacroAnalyticsContext(
        metric="risk_sentiment",
        start_at=0,
        end_at=observed_at,
        latest_observation=observation,
        status=MacroContextStatus.PROVISIONAL,
        observation_count=1,
        conflicted_count=0,
        unknown_count=0,
    )
    binding = (
        MacroContextBinding.for_wallet(subject_id, context)
        if kind == "WALLET"
        else MacroContextBinding.for_token(subject_id, context)
    )
    report = render_persian_macro_markdown(
        MacroContextReadModel.from_binding(binding)
    )
    snapshot = JsonMacroReportSnapshotStore().save(
        report,
        tmp_path / f"{subject_id.replace(':', '_')}.json",
    )
    return DashboardMacroReadResponse.from_report(report, snapshot)


def test_index_searches_filters_sorts_and_pages(tmp_path) -> None:
    index = DashboardMacroReadIndex.from_responses(
        [
            _response("evm:base:token-b", tmp_path),
            _response("evm:base:token-a", tmp_path),
            _response("evm:base:wallet-a", tmp_path, "WALLET"),
        ]
    )

    page = index.page(query="token", subject_kind="TOKEN", offset=0, limit=1)

    assert page.total_count == 2
    assert len(page.items) == 1
    assert page.items[0].subject_id == "evm:base:token-a"
    assert page.has_more is True


def test_index_is_deterministic_and_reports_empty_results(tmp_path) -> None:
    responses = [_response("evm:base:token-a", tmp_path)]
    left = DashboardMacroReadIndex.from_responses(responses).page()
    right = DashboardMacroReadIndex.from_responses(responses).page()

    assert left.page_id == right.page_id
    empty = DashboardMacroReadIndex.from_responses(responses).page(
        query="missing"
    )
    assert empty.items == ()
    assert empty.total_count == 0
    assert empty.has_more is False


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"offset": -1}, "offset"),
        ({"limit": 0}, "limit"),
        ({"query": 1}, "query"),
    ],
)
def test_index_rejects_invalid_query_parameters(
    kwargs: dict[str, object],
    error: str,
) -> None:
    index = DashboardMacroReadIndex.from_responses([])
    with pytest.raises((TypeError, ValueError), match=error):
        index.page(**kwargs)


def test_index_resolves_subject_detail_by_response_and_subject(tmp_path) -> None:
    response = _response("evm:base:token-detail", tmp_path)
    index = DashboardMacroReadIndex.from_responses([response])

    by_response = index.detail(response.response_id)
    by_subject = index.detail_for_subject("evm:base:token-detail")

    assert isinstance(by_response, DashboardSubjectDetail)
    assert by_response.detail_id == by_subject.detail_id
    assert by_subject.subject_id == response.subject_id


def test_index_detail_fails_closed_for_missing_or_ambiguous_subject(tmp_path) -> None:
    first = _response(
        "evm:base:token-duplicate",
        tmp_path / "first",
        observed_at=10,
    )
    second = _response(
        "evm:base:token-duplicate",
        tmp_path / "second",
        observed_at=11,
    )
    index = DashboardMacroReadIndex.from_responses([first, second])

    with pytest.raises(KeyError):
        index.detail("missing")
    with pytest.raises(ValueError, match="ambiguous"):
        index.detail_for_subject("evm:base:token-duplicate")


def test_index_executes_canonical_detail_query(tmp_path) -> None:
    index = DashboardMacroReadIndex.from_responses(
        [
            _response("evm:base:token-b", tmp_path),
            _response("evm:base:token-a", tmp_path),
            _response("evm:base:wallet-a", tmp_path, "WALLET"),
        ]
    )
    query = DashboardSubjectDetailQuery(
        query="TOKEN-A",
        subject_kind="token",
        offset=0,
        limit=1,
    )
    page = index.page_for_query(query)

    assert query.query == "TOKEN-A"
    assert query.subject_kind == "TOKEN"
    assert query.query_id == DashboardSubjectDetailQuery(
        query="TOKEN-A",
        subject_kind="TOKEN",
        offset=0,
        limit=1,
    ).query_id
    assert page.items[0].subject_id == "evm:base:token-a"


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"offset": -1}, "offset"),
        ({"limit": 0}, "limit"),
        ({"query": 1}, "query"),
        ({"subject_kind": 1}, "subject_kind"),
    ],
)
def test_detail_query_rejects_invalid_values(
    kwargs: dict[str, object],
    error: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=error):
        DashboardSubjectDetailQuery(**kwargs)


def test_index_returns_canonical_query_result(tmp_path) -> None:
    index = DashboardMacroReadIndex.from_responses(
        [_response("evm:base:token-result", tmp_path)]
    )
    query = DashboardSubjectDetailQuery(query="token-result")

    result = index.result_for_query(query)

    assert isinstance(result, DashboardQueryResult)
    assert result.status is DashboardQueryResultStatus.SUCCESS
    assert result.query.query_id == query.query_id
    assert result.result_id == index.result_for_query(query).result_id


def test_query_result_reports_empty_without_error(tmp_path) -> None:
    index = DashboardMacroReadIndex.from_responses([])
    result = index.result_for_query(DashboardSubjectDetailQuery(query="none"))

    assert result.status is DashboardQueryResultStatus.EMPTY
    assert result.page.total_count == 0
    assert result.error_code is None
