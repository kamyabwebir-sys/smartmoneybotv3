from contracts import EvidencePayload
from scorer import MarketScorer


def test_scorer_bullish_logic():
    scorer = MarketScorer()
    # شواهد صعودی
    ev1 = EvidencePayload("S1", "market_structure", 100, {"direction": "bullish"})
    ev2 = EvidencePayload("S1", "market_structure", 101, {"direction": "bullish"})

    report = scorer.analyze([ev1, ev2])

    assert report.score == 1.0  # 0.5 + 0.5
    assert report.evidence_count == 2


def test_scorer_neutral_logic():
    scorer = MarketScorer()
    ev = EvidencePayload("S1", "unknown_type", 100, {"direction": "bullish"})
    report = scorer.analyze([ev])

    assert report.score == 0.0  # نوع ناشناخته نباید روی امتیاز اثر بگذارد
