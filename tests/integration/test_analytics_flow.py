from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from contracts import EvidencePayload
from ledger import EvidenceGroundingLedger
from smart_money.application.analytics import (
    AnalyticsOrchestrator as CanonicalOrchestrator,
)
from smart_money.application.replay_integrity import score_report_hash
from smart_money.core.replay import make_replay_manifest


def test_ledger_to_score_flow(tmp_path):
    # 1. آماده‌سازی یک لجر واقعی روی دیسک
    ledger = EvidenceGroundingLedger()
    # ثبت دو واقعه صعودی در لجر
    ledger.record(
        EvidencePayload("S1", "market_structure", 100, {"direction": "bullish"})
    )
    ledger.record(
        EvidencePayload("S1", "market_structure", 101, {"direction": "bullish"})
    )

    path = tmp_path / "integration_ledger.json"
    ledger.save_to_disk(path)

    # 2. اجرای ارکستراتور
    orchestrator = CanonicalOrchestrator(path)
    report = orchestrator.run_full_analysis()

    # 3. تایید اینکه امتیاز نهایی از لجر استخراج شده
    assert report.score == Decimal("1")
    assert report.evidence_count == 2
    assert "Analyzed 2 structure points" in report.reasoning
    assert report.score_breakdown["raw_score"] == Decimal("1.0")
    assert report.score_breakdown["bounded_score"] == Decimal("1")


def test_verified_analysis_binds_real_ledger_and_output_deterministically(tmp_path):
    ledger = EvidenceGroundingLedger()
    ledger.record(
        EvidencePayload("S1", "market_structure", 100, {"direction": "bullish"})
    )
    path = tmp_path / "verified_ledger.json"
    ledger.save_to_disk(path)
    replay_manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash=ledger.content_hash,
        config_hash="config.v1",
    )

    first = CanonicalOrchestrator(path).run_verified_analysis(replay_manifest)
    second = CanonicalOrchestrator(path).run_verified_analysis(replay_manifest)

    assert first == second
    assert first.integrity.input_hash == ledger.content_hash
    assert first.integrity.output_hash == score_report_hash(first.report)
    assert first.integrity.replay_manifest_id == replay_manifest.manifest_id
    assert first.integrity.evidence_count == first.report.evidence_count == 1
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.report = second.report  # type: ignore[misc]


def test_verified_analysis_fails_closed_for_stale_replay_manifest(tmp_path):
    ledger = EvidenceGroundingLedger()
    ledger.record(
        EvidencePayload("S1", "market_structure", 100, {"direction": "bullish"})
    )
    path = tmp_path / "stale_manifest_ledger.json"
    ledger.save_to_disk(path)
    stale_manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="0" * 64,
        config_hash="config.v1",
    )

    orchestrator = CanonicalOrchestrator(path)
    with pytest.raises(ValueError, match="does not match"):
        orchestrator.run_verified_analysis(stale_manifest)
