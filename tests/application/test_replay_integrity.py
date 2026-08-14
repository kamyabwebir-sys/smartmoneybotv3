from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.analytics.scoring import MarketScorer, ScoreReport
from smart_money.application.replay_integrity import (
    ReplayIntegrityError,
    ReplayIntegrityManifest,
    compare_replay_integrity,
    create_replay_integrity_manifest,
    score_report_hash,
    verify_replay_integrity,
)
from smart_money.core.replay import make_replay_manifest
from smart_money.ingestion.contracts import EvidencePayload


def _ledger_and_report(
    direction: str = "bullish",
) -> tuple[EvidenceGroundingLedger, ScoreReport]:
    ledger = EvidenceGroundingLedger()
    ledger.append(
        EvidencePayload(
            source_id="provider.sol",
            evidence_type="market_structure",
            timestamp=1_700_000_000,
            data={"direction": direction, "nested": {"b": 2, "a": 1}},
        )
    )
    return ledger, MarketScorer().analyze(ledger.iter_payloads())


def _integrity_manifest(
    direction: str = "bullish",
    *,
    pipeline_version: str = "pipeline.v1",
    config_hash: str = "config_001",
) -> ReplayIntegrityManifest:
    ledger, report = _ledger_and_report(direction)
    replay_manifest = make_replay_manifest(
        pipeline_version=pipeline_version,
        input_dataset_hash=ledger.content_hash,
        config_hash=config_hash,
    )
    return create_replay_integrity_manifest(
        replay_manifest=replay_manifest,
        ledger_content_hash=ledger.content_hash,
        report=report,
    )


def test_manifest_is_deterministic_frozen_and_slotted() -> None:
    first = _integrity_manifest()
    second = _integrity_manifest()

    assert first == second
    assert first.integrity_id == second.integrity_id
    assert first.schema_version == "replay_integrity.v1"
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.output_hash = "0" * 64  # type: ignore[misc]


def test_manifest_uses_actual_ledger_hash_and_complete_score_report() -> None:
    ledger, report = _ledger_and_report()
    replay_manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash=ledger.content_hash,
        config_hash="config_001",
    )

    integrity = create_replay_integrity_manifest(
        replay_manifest=replay_manifest,
        ledger_content_hash=ledger.content_hash,
        report=report,
    )

    assert integrity.replay_manifest_id == replay_manifest.manifest_id
    assert integrity.input_hash == ledger.content_hash
    assert integrity.output_hash == score_report_hash(report)
    assert integrity.evidence_count == report.evidence_count


def test_score_report_hash_ignores_mapping_insertion_order() -> None:
    first = ScoreReport(
        score=Decimal("0.5"),
        reasoning="stable",
        evidence_count=1,
        score_breakdown={"b": 2, "a": 1},
    )
    second = ScoreReport(
        score=Decimal("0.5"),
        reasoning="stable",
        evidence_count=1,
        score_breakdown={"a": 1, "b": 2},
    )

    assert score_report_hash(first) == score_report_hash(second)


def test_changed_input_or_output_changes_integrity_id() -> None:
    bullish = _integrity_manifest("bullish")
    bearish = _integrity_manifest("bearish")
    different_config = _integrity_manifest("bullish", config_hash="config_002")

    assert bullish.input_hash != bearish.input_hash
    assert bullish.output_hash != bearish.output_hash
    assert bullish.integrity_id != bearish.integrity_id
    assert bullish.integrity_id != different_config.integrity_id


def test_declared_and_actual_ledger_hash_must_match() -> None:
    ledger, report = _ledger_and_report()
    replay_manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="0" * 64,
        config_hash="config_001",
    )

    with pytest.raises(ValueError, match="does not match"):
        create_replay_integrity_manifest(
            replay_manifest=replay_manifest,
            ledger_content_hash=ledger.content_hash,
            report=report,
        )


@pytest.mark.parametrize("field", ["input_hash", "output_hash"])
def test_manifest_rejects_malformed_integrity_hashes(field: str) -> None:
    valid = _integrity_manifest()
    values = valid.canonical_dict()
    values[field] = "NOT-A-SHA256"

    with pytest.raises(ValueError, match="lowercase SHA-256"):
        ReplayIntegrityManifest(**values)


def test_manifest_rejects_forged_deterministic_id() -> None:
    valid = _integrity_manifest()
    values = valid.canonical_dict()
    values["integrity_id"] = "replay_integrity_forged"

    with pytest.raises(ValueError, match="integrity_id"):
        ReplayIntegrityManifest(**values)


def test_identical_manifests_compare_successfully() -> None:
    expected = _integrity_manifest()
    comparison = verify_replay_integrity(expected, expected)

    assert comparison.matches is True
    assert comparison.mismatch_fields == ()
    assert comparison == compare_replay_integrity(expected, expected)


def test_mismatch_report_is_deterministic_and_verification_fails_closed() -> None:
    expected = _integrity_manifest("bullish", pipeline_version="pipeline.v1")
    actual = _integrity_manifest("bearish", pipeline_version="pipeline.v2")

    comparison = compare_replay_integrity(expected, actual)

    assert comparison.matches is False
    assert comparison.mismatch_fields == tuple(sorted(comparison.mismatch_fields))
    assert comparison.mismatch_fields == (
        "input_hash",
        "output_hash",
        "pipeline_version",
        "replay_manifest_id",
    )
    assert comparison == compare_replay_integrity(expected, actual)

    with pytest.raises(ReplayIntegrityError) as exc_info:
        verify_replay_integrity(expected, actual)

    assert exc_info.value.comparison == comparison
    assert str(exc_info.value) == (
        "replay integrity mismatch: "
        "input_hash, output_hash, pipeline_version, replay_manifest_id"
    )
