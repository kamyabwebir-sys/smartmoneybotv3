import analytics_orchestrator as legacy_analytics
import contracts as legacy_contracts
import ledger as legacy_ledger
import population as legacy_population
import provider as legacy_provider
import replay_engine as legacy_replay
import scorer as legacy_scorer
from smart_money.adapters.persistence.json_ledger import (
    EvidenceGroundingLedger,
    GroundedEntry,
)
from smart_money.analytics.scoring import MarketScorer, ScoreReport
from smart_money.application.analytics import AnalyticsOrchestrator
from smart_money.application.population import EvidencePopulator
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.replay import ReplayEngine
from smart_money.ingestion.contracts import EvidencePayload, IngestionResult
from smart_money.ingestion.ledger import EvidenceLedger as LegacyEvidenceLedger
from smart_money.ingestion.provider import EvidenceIngestionProvider


def test_legacy_facades_reexport_canonical_objects() -> None:
    expected_exports = (
        (legacy_analytics.AnalyticsOrchestrator, AnalyticsOrchestrator),
        (legacy_contracts.EvidencePayload, EvidencePayload),
        (legacy_contracts.GroundedEntry, GroundedEntry),
        (legacy_contracts.IngestionResult, IngestionResult),
        (legacy_contracts.ScoreReport, ScoreReport),
        (legacy_ledger.EvidenceGroundingLedger, EvidenceGroundingLedger),
        (legacy_population.EvidencePopulator, EvidencePopulator),
        (legacy_provider.EvidenceIngestionProvider, EvidenceIngestionProvider),
        (legacy_replay.ReplayEngine, ReplayEngine),
        (legacy_scorer.MarketScorer, MarketScorer),
        (legacy_scorer.ScoreReport, ScoreReport),
        (LegacyEvidenceLedger, EvidenceLedger),
    )

    for legacy_object, canonical_object in expected_exports:
        assert legacy_object is canonical_object

    assert legacy_analytics.__all__ == ["AnalyticsOrchestrator"]
    assert legacy_contracts.__all__ == [
        "EvidencePayload",
        "GroundedEntry",
        "IngestionResult",
        "ScoreReport",
    ]
    assert legacy_ledger.__all__ == ["EvidenceGroundingLedger"]
    assert legacy_population.__all__ == ["EvidencePopulator"]
    assert legacy_provider.__all__ == ["EvidenceIngestionProvider"]
    assert legacy_replay.__all__ == ["ReplayEngine"]
    assert legacy_scorer.__all__ == ["MarketScorer", "ScoreReport"]
