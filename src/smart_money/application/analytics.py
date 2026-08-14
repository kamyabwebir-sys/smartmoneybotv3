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
from smart_money.application.score_traceability import (
    ScoreEvidenceTrace,
    create_score_evidence_trace,
)
from smart_money.core.replay import ReplayManifest


@dataclass(frozen=True, slots=True)
class ReplayAnalysisResult:
    """Immutable analytical output paired with its replay integrity receipt."""

    report: ScoreReport
    integrity: ReplayIntegrityManifest
    trace: ScoreEvidenceTrace

    def __post_init__(self) -> None:
        if not isinstance(self.report, ScoreReport):
            raise TypeError("report must be a ScoreReport")
        if not isinstance(self.integrity, ReplayIntegrityManifest):
            raise TypeError("integrity must be a ReplayIntegrityManifest")
        if not isinstance(self.trace, ScoreEvidenceTrace):
            raise TypeError("trace must be a ScoreEvidenceTrace")
        if self.report.evidence_count != self.integrity.evidence_count:
            raise ValueError("report and integrity evidence counts do not match")
        if score_report_hash(self.report) != self.integrity.output_hash:
            raise ValueError("report does not match replay integrity output hash")
        if self.trace.integrity_id != self.integrity.integrity_id:
            raise ValueError("trace and replay integrity IDs do not match")
        if self.trace.replay_manifest_id != self.integrity.replay_manifest_id:
            raise ValueError("trace and replay manifest IDs do not match")
        if self.trace.ledger_content_hash != self.integrity.input_hash:
            raise ValueError("trace and ledger hashes do not match")
        if self.trace.score_output_hash != self.integrity.output_hash:
            raise ValueError("trace and score output hashes do not match")
        if len(self.trace.contributions) != self.report.evidence_count:
            raise ValueError("trace and report evidence counts do not match")


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
        evidence = tuple(self.engine.stream_captured_evidence())
        report = self.scorer.analyze(evidence)
        integrity = create_replay_integrity_manifest(
            replay_manifest=replay_manifest,
            ledger_content_hash=self.engine.content_hash,
            report=report,
        )
        trace = create_score_evidence_trace(
            evidence=evidence,
            report=report,
            replay_manifest=replay_manifest,
            integrity=integrity,
            ledger_content_hash=self.engine.content_hash,
        )
        return ReplayAnalysisResult(
            report=report,
            integrity=integrity,
            trace=trace,
        )


__all__ = ["AnalyticsOrchestrator"]
