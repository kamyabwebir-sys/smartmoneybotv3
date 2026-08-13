import os
from ledger import EvidenceGroundingLedger
from contracts import EvidencePayload
from analytics_orchestrator import AnalyticsOrchestrator


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

    path = os.path.join(tmp_path, "integration_ledger.json")
    ledger.save_to_disk(path)

    # 2. اجرای ارکستراتور
    orchestrator = AnalyticsOrchestrator(path)
    report = orchestrator.run_full_analysis()

    # 3. تایید اینکه امتیاز نهایی از لجر استخراج شده
    assert report.score == 1.0
    assert report.evidence_count == 2
    assert "Analyzed 2 structure points" in report.reasoning
