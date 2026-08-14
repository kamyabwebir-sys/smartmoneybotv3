from dataclasses import FrozenInstanceError, replace
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
    assert first.trace.integrity_id == first.integrity.integrity_id
    assert first.trace.ledger_content_hash == ledger.content_hash
    assert first.trace.score_output_hash == first.integrity.output_hash
    assert len(first.trace.contributions) == 1
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


def test_trace_maps_every_score_component_to_canonical_evidence(tmp_path):
    evidence = (
        EvidencePayload(
            "provider.sol",
            "market_structure",
            100,
            {"direction": "bullish"},
        ),
        EvidencePayload(
            "provider.base",
            "market_structure",
            101,
            {"direction": "bearish"},
        ),
        EvidencePayload(
            "provider.sol",
            "market_structure",
            102,
            {"direction": "neutral"},
        ),
        EvidencePayload(
            "provider.base",
            "market_structure",
            103,
            {"direction": "uncertain"},
        ),
        EvidencePayload(
            "provider.sol",
            "wallet_activity",
            104,
            {"direction": "bullish"},
        ),
    )
    ledger = EvidenceGroundingLedger()
    for item in evidence:
        ledger.record(item)
    path = tmp_path / "traceable-ledger.json"
    ledger.save_to_disk(path)
    replay_manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash=ledger.content_hash,
        config_hash="config.v1",
    )

    result = CanonicalOrchestrator(path).run_verified_analysis(replay_manifest)
    contributions = result.trace.contributions
    by_component = {item.score_component: item for item in contributions}

    assert tuple(item.evidence_id for item in contributions) == tuple(
        sorted(item.get_canonical_id() for item in evidence)
    )
    assert by_component["bullish_count"].status == "scored"
    assert by_component["bullish_count"].score_delta == Decimal("0.5")
    assert by_component["bearish_count"].status == "scored"
    assert by_component["bearish_count"].score_delta == Decimal("-0.5")
    assert by_component["neutral_count"].status == "zero_weight"
    assert by_component["unknown_direction_count"].status == "zero_weight"
    assert by_component["ignored_evidence_count"].status == "ignored"
    assert all(
        set(item.canonical_dict())
        == {
            "evidence_id",
            "source_id",
            "evidence_type",
            "timestamp",
            "status",
            "score_component",
            "score_delta",
        }
        for item in contributions
    )
    assert not hasattr(result.trace, "__dict__")
    assert not hasattr(contributions[0], "__dict__")
    with pytest.raises(FrozenInstanceError):
        contributions[0].status = "ignored"  # type: ignore[misc]
    with pytest.raises(ValueError, match="score_delta"):
        replace(
            by_component["bullish_count"],
            score_delta=Decimal("1"),
        )
    with pytest.raises(ValueError, match="trace_id"):
        replace(result.trace, trace_id="score_evidence_trace_forged")


def test_trace_contributions_are_order_stable_but_keep_ledger_identity(tmp_path):
    evidence = (
        EvidencePayload(
            "provider.sol",
            "market_structure",
            100,
            {"direction": "bullish"},
        ),
        EvidencePayload(
            "provider.base",
            "market_structure",
            101,
            {"direction": "bearish"},
        ),
    )

    results = []
    for index, ordered in enumerate((evidence, tuple(reversed(evidence)))):
        ledger = EvidenceGroundingLedger()
        for item in ordered:
            ledger.record(item)
        path = tmp_path / f"ordered-{index}.json"
        ledger.save_to_disk(path)
        replay_manifest = make_replay_manifest(
            pipeline_version="pipeline.v1",
            input_dataset_hash=ledger.content_hash,
            config_hash="config.v1",
        )
        results.append(
            CanonicalOrchestrator(path).run_verified_analysis(replay_manifest)
        )

    first, second = results
    assert first.report == second.report
    assert first.trace.contributions == second.trace.contributions
    assert first.trace.ledger_content_hash != second.trace.ledger_content_hash
    assert first.trace.trace_id != second.trace.trace_id
