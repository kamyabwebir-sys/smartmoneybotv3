from __future__ import annotations

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.analytics import AnalyticsOrchestrator
from smart_money.core.replay import make_replay_manifest
from smart_money.ingestion.contracts import EvidencePayload
from smart_money.reporting.audit_trail_generator import (
    render_markdown_audit_trail,
    write_markdown_audit_trail,
)


def _analysis_result(tmp_path):
    ledger = EvidenceGroundingLedger()
    ledger.append(
        EvidencePayload(
            source_id="provider|sol",
            evidence_type="market_structure",
            timestamp=100,
            data={"direction": "bullish", "private_raw": "must-not-leak"},
        )
    )
    ledger.append(
        EvidencePayload(
            source_id="provider.base",
            evidence_type="market_structure",
            timestamp=101,
            data={"direction": "neutral"},
        )
    )
    ledger.append(
        EvidencePayload(
            source_id="provider.sol",
            evidence_type="wallet_activity",
            timestamp=102,
            data={"wallet": "secret-wallet", "direction": "bullish"},
        )
    )
    ledger_path = tmp_path / "audit-ledger.json"
    ledger.save_to_disk(ledger_path)
    replay_manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash=ledger.content_hash,
        config_hash="config.v1",
    )
    return AnalyticsOrchestrator(ledger_path).run_verified_analysis(
        replay_manifest
    )


def test_markdown_audit_trail_contains_verified_identity_and_tables(tmp_path) -> None:
    result = _analysis_result(tmp_path)

    report = render_markdown_audit_trail(result)

    assert report.startswith("# Replay Analysis Audit Trail\n")
    assert "markdown_audit_trail.v1" in report
    assert result.trace.trace_id in report
    assert result.integrity.integrity_id in report
    assert result.trace.ledger_content_hash in report
    assert result.trace.score_output_hash in report
    assert "## Confirmed Scoring Evidence" in report
    assert "## Rejected or Non-Contributing Evidence" in report
    assert "| bullish_count | 1 |" in report
    assert "| ignored_evidence_count | 1 |" in report
    assert "| neutral_count | 1 |" in report
    assert "provider\\|sol" in report


def test_markdown_uses_trace_references_without_leaking_raw_evidence(tmp_path) -> None:
    result = _analysis_result(tmp_path)

    report = render_markdown_audit_trail(result)

    assert all(
        contribution.evidence_id in report
        for contribution in result.trace.contributions
    )
    assert "must-not-leak" not in report
    assert "secret-wallet" not in report
    assert "private_raw" not in report
    assert '"direction"' not in report


def test_markdown_render_and_write_are_byte_stable(tmp_path) -> None:
    result = _analysis_result(tmp_path)
    first_path = tmp_path / "first" / "audit.md"
    second_path = tmp_path / "second" / "audit.md"

    first_render = render_markdown_audit_trail(result)
    second_render = render_markdown_audit_trail(result)
    returned_path = write_markdown_audit_trail(result, first_path)
    write_markdown_audit_trail(result, second_path)

    assert first_render == second_render
    assert returned_path == first_path
    assert first_path.read_bytes() == second_path.read_bytes()
    assert first_path.read_bytes() == first_render.encode("utf-8")
    assert b"\r\n" not in first_path.read_bytes()


def test_markdown_preserves_canonical_trace_order(tmp_path) -> None:
    result = _analysis_result(tmp_path)

    report = render_markdown_audit_trail(result)
    for scored in (True, False):
        group = tuple(
            item
            for item in result.trace.contributions
            if (item.status == "scored") is scored
        )
        positions = [report.index(item.evidence_id) for item in group]
        assert positions == sorted(positions)


def test_renderer_rejects_non_verified_result() -> None:
    try:
        render_markdown_audit_trail(object())  # type: ignore[arg-type]
    except TypeError as exc:
        assert str(exc) == "result must be a ReplayAnalysisResult"
    else:
        raise AssertionError("renderer accepted a non-verified result")
