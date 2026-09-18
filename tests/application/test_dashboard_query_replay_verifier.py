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
from smart_money.application.dashboard_query_endpoint import (
    DashboardQueryEndpoint,
)
from smart_money.application.dashboard_query_replay_verifier import (
    DashboardQueryReplayVerifier,
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


def _response(tmp_path, subject_id: str, observed_at: int = 10):
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
    report = render_persian_macro_markdown(
        MacroContextReadModel.from_binding(
            MacroContextBinding.for_token(subject_id, context)
        )
    )
    snapshot = JsonMacroReportSnapshotStore().save(
        report,
        tmp_path / "macro-report.json",
    )
    return DashboardMacroReadResponse.from_report(report, snapshot)


def test_replay_verifier_confirms_identical_receipt(tmp_path) -> None:
    response = _response(tmp_path, "evm:base:token-replay")
    endpoint = DashboardQueryEndpoint(
        DashboardMacroReadIndex.from_responses([response])
    )
    query = DashboardSubjectDetailQuery(query="replay")
    _, expected = endpoint.execute_with_receipt(query)

    verification = DashboardQueryReplayVerifier(endpoint).verify(query, expected)

    assert verification.matches is True
    assert verification.mismatches == ()
    assert verification.verification_id == (
        DashboardQueryReplayVerifier(endpoint).verify(query, expected).verification_id
    )


def test_replay_verifier_reports_drift(tmp_path) -> None:
    first = _response(tmp_path / "first", "evm:base:token-replay")
    endpoint = DashboardQueryEndpoint(
        DashboardMacroReadIndex.from_responses([first])
    )
    query = DashboardSubjectDetailQuery(query="replay")
    _, expected = endpoint.execute_with_receipt(query)
    changed = _response(tmp_path / "changed", "evm:base:token-replay", 11)
    changed_endpoint = DashboardQueryEndpoint(
        DashboardMacroReadIndex.from_responses([changed])
    )

    verification = DashboardQueryReplayVerifier(changed_endpoint).verify(
        query,
        expected,
    )

    assert verification.matches is False
    assert "output_hash" in verification.mismatches
