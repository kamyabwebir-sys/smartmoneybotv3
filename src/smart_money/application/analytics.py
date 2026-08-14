from __future__ import annotations

from pathlib import Path

from smart_money.analytics.scoring import MarketScorer, ScoreReport
from smart_money.application.replay import ReplayEngine


class AnalyticsOrchestrator:
    """Coordinate persisted evidence replay and deterministic analytics."""

    def __init__(self, ledger_path: str | Path) -> None:
        self.engine = ReplayEngine(ledger_path)
        self.scorer = MarketScorer()

    def run_full_analysis(self) -> ScoreReport:
        return self.scorer.analyze(self.engine.stream_captured_evidence())


__all__ = ["AnalyticsOrchestrator"]
