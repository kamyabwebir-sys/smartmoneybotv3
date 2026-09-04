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
from smart_money.application.dashboard_audit_recovery_gate import (
    DashboardAuditRecoveryReceipt,
)
from smart_money.application.dashboard_macro_read_endpoint import (
    DashboardMacroReadResponse,
)
from smart_money.application.dashboard_macro_read_index import (
    DashboardMacroReadIndex,
)
from smart_money.application.dashboard_query_endpoint import (
    DashboardQueryEndpoint,
)
from smart_money.application.dashboard_query_result import (
    DashboardQueryResult,
)
from smart_money.application.dashboard_recovery_query_session import (
    DashboardRecoveryQuerySession,
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


def _endpoint(tmp_path):
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
    report = render_persian_macro_markdown(
        MacroContextReadModel.from_binding(
            MacroContextBinding.for_token("evm:base:token-session", context)
        )
    )
    snapshot = JsonMacroReportSnapshotStore().save(
        report,
        tmp_path / "report.json",
    )
    response = DashboardMacroReadResponse.from_report(report, snapshot)
    return DashboardQueryEndpoint(DashboardMacroReadIndex.from_responses([response]))


def test_session_executes_only_when_recovery_is_ready(tmp_path) -> None:
    session = DashboardRecoveryQuerySession(_endpoint(tmp_path))
    recovery = DashboardAuditRecoveryReceipt(
        decision="READY",
        reason_code="CHAIN_HEAD_VERIFIED",
        anchor_id="anchor",
        chain_id="chain",
    )

    outcome, query_receipt, session_receipt = session.execute(
        recovery,
        DashboardSubjectDetailQuery(query="session"),
    )

    assert isinstance(outcome, DashboardQueryResult)
    assert query_receipt is not None
    assert session_receipt.session_status == "EXECUTED"
    assert session_receipt.query_id == outcome.query.query_id


def test_session_blocks_without_calling_query_endpoint(tmp_path) -> None:
    session = DashboardRecoveryQuerySession(_endpoint(tmp_path))
    recovery = DashboardAuditRecoveryReceipt(
        decision="BLOCKED",
        reason_code="CHAIN_HEAD_MISMATCH",
        anchor_id="anchor",
        chain_id="chain",
    )

    outcome, query_receipt, session_receipt = session.execute(
        recovery,
        DashboardSubjectDetailQuery(query="session"),
    )

    assert outcome is None
    assert query_receipt is None
    assert session_receipt.session_status == "BLOCKED"
    assert session_receipt.reason_code == "RECOVERY_GATE_BLOCKED"
