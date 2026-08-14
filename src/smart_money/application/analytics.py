from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from smart_money.analytics.scoring import MarketScorer, ScoreReport
from smart_money.application.replay import ReplayEngine
from smart_money.application.replay_integrity import (
    ReplayIntegrityManifest,
    create_replay_integrity_manifest,
    score_report_hash,
)
from smart_money.core.replay import ReplayManifest


@dataclass(frozen=True, slots=True)
class ReplayAnalysisResult:
    """Immutable analytical output paired with its replay integrity receipt."""

    report: ScoreReport
    integrity: ReplayIntegrityManifest

    def __post_init__(self) -> None:
        if not isinstance(self.report, ScoreReport):
            raise TypeError("report must be a ScoreReport")
        if not isinstance(self.integrity, ReplayIntegrityManifest):
            raise TypeError("integrity must be a ReplayIntegrityManifest")
        if self.report.evidence_count != self.integrity.evidence_count:
            raise ValueError("report and integrity evidence counts do not match")
        if score_report_hash(self.report) != self.integrity.output_hash:
            raise ValueError("report does not match replay integrity output hash")


class AnalyticsOrchestrator:
    """Coordinate persisted evidence replay and deterministic analytics."""

    def __init__(self, ledger_path: str | Path) -> None:
        self.engine = ReplayEngine(ledger_path)
        self.scorer = MarketScorer()

    def run_full_analysis(self) -> ScoreReport:
        return self.scorer.analyze(self.engine.stream_captured_evidence())

    def run_verified_analysis(
        self,
        replay_manifest: ReplayManifest,
    ) -> ReplayAnalysisResult:
        """Analyze persisted evidence and bind the output to an integrity receipt."""
        report = self.run_full_analysis()
        integrity = create_replay_integrity_manifest(
            replay_manifest=replay_manifest,
            ledger_content_hash=self.engine.content_hash,
            report=report,
        )
        return ReplayAnalysisResult(report=report, integrity=integrity)


__all__ = ["AnalyticsOrchestrator"]
