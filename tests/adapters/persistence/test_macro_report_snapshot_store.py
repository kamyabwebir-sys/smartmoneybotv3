import json
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


def test_snapshot_is_atomic_byte_stable_and_replayable(tmp_path) -> None:
    path = tmp_path / "macro-report.json"
    store = JsonMacroReportSnapshotStore()
    report = _report()

    snapshot = store.save(report, path)
    first_bytes = path.read_bytes()
    restored = store.load(path)
    receipt = store.replay(report, restored)
    store.save(report, path)

    assert path.read_bytes() == first_bytes
    assert restored == snapshot
    assert receipt.matches is True
    assert receipt.content_hash == snapshot.content_hash


def test_snapshot_corruption_is_rejected(tmp_path) -> None:
    path = tmp_path / "macro-report.json"
    store = JsonMacroReportSnapshotStore()
    store.save(_report(), path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["content_hash"] = "0" * 64
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        store.load(path)


def test_replay_rejects_changed_report() -> None:
    store = JsonMacroReportSnapshotStore()
    report = _report()
    snapshot = store.save(report, "macro-report-test.json")
    changed = type(report)(
        model_id=report.model_id,
        explanation_id=report.explanation_id,
        subject_id=report.subject_id,
        markdown=report.markdown + "\n",
    )
    try:
        with pytest.raises(ValueError, match="does not match"):
            store.replay(changed, snapshot)
    finally:
        import os

        if os.path.exists("macro-report-test.json"):
            os.remove("macro-report-test.json")
