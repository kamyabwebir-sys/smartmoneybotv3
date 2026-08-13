from __future__ import annotations

from pathlib import Path

from contracts import ScoreReport
from replay_engine import ReplayEngine
from scorer import MarketScorer


class AnalyticsOrchestrator:
    """Connect persisted evidence replay to deterministic analytical scoring."""

    def __init__(self, ledger_path: str | Path) -> None:
        self.engine = ReplayEngine(ledger_path)
        self.scorer = MarketScorer()

    def run_full_analysis(self) -> ScoreReport:
        return self.scorer.analyze(self.engine.stream_captured_evidence())
