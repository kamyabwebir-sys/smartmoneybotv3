from decimal import Decimal
from types import MappingProxyType

import pytest

from contracts import EvidencePayload
from contracts import ScoreReport as LegacyScoreReport
from scorer import MarketScorer as LegacyMarketScorer
from smart_money.analytics.scoring import MarketScorer as CanonicalMarketScorer
from smart_money.analytics.scoring import ScoreReport as CanonicalScoreReport


def test_legacy_and_canonical_imports_are_identical():
    assert LegacyMarketScorer is CanonicalMarketScorer
    assert LegacyScoreReport is CanonicalScoreReport


def test_scorer_bullish_logic():
    scorer = CanonicalMarketScorer()
    # شواهد صعودی
    ev1 = EvidencePayload("S1", "market_structure", 100, {"direction": "bullish"})
    ev2 = EvidencePayload("S1", "market_structure", 101, {"direction": "bullish"})

    report = scorer.analyze([ev1, ev2])

    assert report.score == Decimal("1")  # 0.5 + 0.5
    assert report.evidence_count == 2


def test_scorer_neutral_logic():
    scorer = CanonicalMarketScorer()
    ev = EvidencePayload("S1", "unknown_type", 100, {"direction": "bullish"})
    report = scorer.analyze([ev])

    assert report.score == Decimal("0")  # نوع ناشناخته نباید روی امتیاز اثر بگذارد


def test_score_breakdown_is_deterministic_and_deeply_immutable():
    scorer = CanonicalMarketScorer()
    evidence = [
        EvidencePayload("S1", "market_structure", 100, {"direction": "bullish"}),
        EvidencePayload("S1", "market_structure", 101, {"direction": "bearish"}),
        EvidencePayload("S1", "market_structure", 102, {"direction": "neutral"}),
        EvidencePayload("S1", "market_structure", 103, {"direction": "unknown"}),
        EvidencePayload("S1", "other", 104, {"direction": "bullish"}),
    ]

    forward = scorer.analyze(evidence)
    reverse = scorer.analyze(reversed(evidence))

    expected = {
        "bearish_count": 1,
        "bounded_score": Decimal("0"),
        "bullish_count": 1,
        "evidence_count": 5,
        "ignored_evidence_count": 1,
        "neutral_count": 1,
        "raw_score": Decimal("0"),
        "structure_count": 4,
        "unknown_direction_count": 1,
    }
    assert forward.score_breakdown == expected
    assert reverse.score_breakdown == expected
    assert isinstance(forward.score_breakdown, MappingProxyType)

    with pytest.raises(TypeError):
        forward.score_breakdown["raw_score"] = Decimal("1")


def test_breakdown_preserves_raw_score_before_bounding():
    scorer = CanonicalMarketScorer()
    evidence = [
        EvidencePayload(
            "S1",
            "market_structure",
            timestamp,
            {"direction": "bullish"},
        )
        for timestamp in range(100, 104)
    ]

    report = scorer.analyze(evidence)

    assert report.score == Decimal("1")
    assert report.score_breakdown["raw_score"] == Decimal("2.0")
    assert report.score_breakdown["bounded_score"] == Decimal("1")
