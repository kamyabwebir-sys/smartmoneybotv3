from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from smart_money.core.audit import (
    DecisionTrace,
    EvidenceRef,
    RejectReason,
    RuleHit,
    make_decision_trace,
)
from smart_money.core.serialization import canonical_json


def _evidence_a() -> EvidenceRef:
    return EvidenceRef(
        kind="candle",
        ref_id="candle_001",
        label="base-candle",
        metadata_json='{"a":1,"b":2}',
    )


def _evidence_b() -> EvidenceRef:
    return EvidenceRef(
        kind="structure_event",
        ref_id="event_001",
        label="event-a",
        metadata_json='{"x":"y"}',
    )


def test_evidence_ref_requires_canonical_metadata_json() -> None:
    with pytest.raises(ValueError, match="canonical JSON"):
        EvidenceRef(
            kind="candle",
            ref_id="candle_001",
            metadata_json='{"b":2,"a":1}',
        )


def test_default_tuples_are_immutable_and_deterministic() -> None:
    hit = RuleHit(rule_code="rule.a", summary="summary")
    reject = RejectReason(code="reject.a", message="message")
    trace = make_decision_trace(subject_id="subject_1", stage="setup")

    assert hit.evidence == ()
    assert reject.evidence == ()
    assert trace.hits == ()
    assert trace.rejects == ()
    assert trace.context_refs == ()


def test_rulehit_score_requires_decimal_not_float() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        RuleHit(
            rule_code="rule.a",
            summary="summary",
            score=1.25,  # type: ignore[arg-type]
        )


def test_trace_id_is_stable_for_equivalent_payloads() -> None:
    hit1 = RuleHit(
        rule_code="rule.a",
        summary="summary-a",
        evidence=(_evidence_b(), _evidence_a()),
        score=Decimal("1.00"),
    )
    reject1 = RejectReason(
        code="reject.a",
        message="message-a",
        evidence=(_evidence_b(), _evidence_a()),
    )

    first = make_decision_trace(
        subject_id="subject_1",
        stage="decision",
        hits=(hit1,),
        rejects=(reject1,),
        context_refs=(_evidence_b(), _evidence_a()),
    )

    hit2 = RuleHit(
        rule_code="rule.a",
        summary="summary-a",
        evidence=(_evidence_a(), _evidence_b()),
        score=Decimal("1.0"),
    )
    reject2 = RejectReason(
        code="reject.a",
        message="message-a",
        evidence=(_evidence_a(), _evidence_b()),
    )

    second = make_decision_trace(
        subject_id="subject_1",
        stage="decision",
        hits=(hit2,),
        rejects=(reject2,),
        context_refs=(_evidence_a(), _evidence_b()),
    )

    assert first.trace_id == second.trace_id


def test_trace_id_changes_when_payload_changes() -> None:
    first = make_decision_trace(
        subject_id="subject_1",
        stage="decision",
        hits=(RuleHit(rule_code="rule.a", summary="summary-a"),),
    )
    second = make_decision_trace(
        subject_id="subject_1",
        stage="decision",
        hits=(RuleHit(rule_code="rule.b", summary="summary-a"),),
    )

    assert first.trace_id != second.trace_id


def test_decision_trace_is_immutable() -> None:
    trace = make_decision_trace(subject_id="subject_1", stage="decision")
    with pytest.raises(FrozenInstanceError):
        trace.stage = "setup"  # type: ignore[misc]


def test_manual_wrong_trace_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="trace_id"):
        DecisionTrace(
            trace_id="decision_trace_wrong",
            subject_id="subject_1",
            stage="decision",
        )


def test_canonical_serialization_for_audit_contracts_is_stable() -> None:
    trace = make_decision_trace(
        subject_id="subject_1",
        stage="decision",
        hits=(
            RuleHit(
                rule_code="rule.a",
                summary="summary-a",
                evidence=(_evidence_a(),),
                score=Decimal("2.00"),
            ),
        ),
        rejects=(
            RejectReason(
                code="reject.a",
                message="message-a",
                evidence=(_evidence_b(),),
            ),
        ),
        context_refs=(_evidence_b(), _evidence_a()),
    )

    first = canonical_json(trace.canonical_dict())
    second = canonical_json(trace.canonical_dict())

    assert first == second
