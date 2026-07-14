from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .ids import deterministic_id
from .serialization import canonical_json, canonicalize


def _require_non_empty_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")

    return normalized


def _require_optional_text(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_text(value, field_name)


def _require_optional_decimal(value: Decimal | None, field_name: str) -> Decimal | None:
    if value is None:
        return None

    if isinstance(value, float):
        raise TypeError(f"{field_name} must be Decimal, not float")

    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal")

    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")

    return value


def _normalize_evidence_refs(value: tuple["EvidenceRef", ...], field_name: str) -> tuple["EvidenceRef", ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")

    for item in value:
        if not isinstance(item, EvidenceRef):
            raise TypeError(f"{field_name} items must be EvidenceRef")

    return tuple(sorted(value, key=lambda item: canonical_json(item.canonical_dict())))


def _validate_canonical_json_text(value: str) -> str:
    parsed = json.loads(value)
    canonical = canonical_json(parsed)
    if canonical != value:
        raise ValueError("metadata_json must already be canonical JSON text")
    return value


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    kind: str
    ref_id: str
    label: str | None = None
    metadata_json: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _require_non_empty_text(self.kind, "kind"))
        object.__setattr__(self, "ref_id", _require_non_empty_text(self.ref_id, "ref_id"))
        object.__setattr__(self, "label", _require_optional_text(self.label, "label"))

        if self.metadata_json is not None:
            if not isinstance(self.metadata_json, str):
                raise TypeError("metadata_json must be a string")
            object.__setattr__(
                self,
                "metadata_json",
                _validate_canonical_json_text(self.metadata_json),
            )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "ref_id": self.ref_id,
            "label": self.label,
            "metadata_json": self.metadata_json,
        }


@dataclass(frozen=True, slots=True)
class RejectReason:
    code: str
    message: str
    evidence: tuple[EvidenceRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _require_non_empty_text(self.code, "code"))
        object.__setattr__(self, "message", _require_non_empty_text(self.message, "message"))
        object.__setattr__(self, "evidence", _normalize_evidence_refs(self.evidence, "evidence"))

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "evidence": tuple(item.canonical_dict() for item in self.evidence),
        }


@dataclass(frozen=True, slots=True)
class RuleHit:
    rule_code: str
    summary: str
    evidence: tuple[EvidenceRef, ...] = ()
    score: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_code", _require_non_empty_text(self.rule_code, "rule_code"))
        object.__setattr__(self, "summary", _require_non_empty_text(self.summary, "summary"))
        object.__setattr__(self, "evidence", _normalize_evidence_refs(self.evidence, "evidence"))
        object.__setattr__(self, "score", _require_optional_decimal(self.score, "score"))

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "rule_code": self.rule_code,
            "summary": self.summary,
            "evidence": tuple(item.canonical_dict() for item in self.evidence),
            "score": self.score,
        }


@dataclass(frozen=True, slots=True)
class DecisionTrace:
    trace_id: str
    subject_id: str
    stage: str
    hits: tuple[RuleHit, ...] = ()
    rejects: tuple[RejectReason, ...] = ()
    context_refs: tuple[EvidenceRef, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "trace_id", _require_non_empty_text(self.trace_id, "trace_id"))
        object.__setattr__(self, "subject_id", _require_non_empty_text(self.subject_id, "subject_id"))
        object.__setattr__(self, "stage", _require_non_empty_text(self.stage, "stage"))

        if not isinstance(self.hits, tuple):
            raise TypeError("hits must be a tuple")
        if not isinstance(self.rejects, tuple):
            raise TypeError("rejects must be a tuple")

        for item in self.hits:
            if not isinstance(item, RuleHit):
                raise TypeError("hits items must be RuleHit")

        for item in self.rejects:
            if not isinstance(item, RejectReason):
                raise TypeError("rejects items must be RejectReason")

        object.__setattr__(
            self,
            "hits",
            tuple(sorted(self.hits, key=lambda item: canonical_json(item.canonical_dict()))),
        )
        object.__setattr__(
            self,
            "rejects",
            tuple(sorted(self.rejects, key=lambda item: canonical_json(item.canonical_dict()))),
        )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_evidence_refs(self.context_refs, "context_refs"),
        )

        expected_trace_id = deterministic_id("decision_trace", self.identity_payload())
        if self.trace_id != expected_trace_id:
            raise ValueError("trace_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "stage": self.stage,
            "hits": tuple(item.canonical_dict() for item in self.hits),
            "rejects": tuple(item.canonical_dict() for item in self.rejects),
            "context_refs": tuple(item.canonical_dict() for item in self.context_refs),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            **self.identity_payload(),
        }


def make_decision_trace(
    *,
    subject_id: str,
    stage: str,
    hits: tuple[RuleHit, ...] = (),
    rejects: tuple[RejectReason, ...] = (),
    context_refs: tuple[EvidenceRef, ...] = (),
) -> DecisionTrace:
    payload = {
        "subject_id": _require_non_empty_text(subject_id, "subject_id"),
        "stage": _require_non_empty_text(stage, "stage"),
        "hits": tuple(item.canonical_dict() for item in sorted(hits, key=lambda x: canonical_json(x.canonical_dict()))),
        "rejects": tuple(item.canonical_dict() for item in sorted(rejects, key=lambda x: canonical_json(x.canonical_dict()))),
        "context_refs": tuple(
            item.canonical_dict()
            for item in sorted(context_refs, key=lambda x: canonical_json(x.canonical_dict()))
        ),
    }
    trace_id = deterministic_id("decision_trace", payload)
    return DecisionTrace(
        trace_id=trace_id,
        subject_id=subject_id,
        stage=stage,
        hits=hits,
        rejects=rejects,
        context_refs=context_refs,
    )
