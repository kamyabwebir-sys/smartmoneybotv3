from decimal import Decimal

from analytics_orchestrator import AnalyticsOrchestrator as LegacyOrchestrator
from contracts import EvidencePayload
from ledger import EvidenceGroundingLedger
from smart_money.application.analytics import (
    AnalyticsOrchestrator as CanonicalOrchestrator,
)


def test_legacy_and_canonical_orchestrator_imports_are_identical():
    assert LegacyOrchestrator is CanonicalOrchestrator


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
