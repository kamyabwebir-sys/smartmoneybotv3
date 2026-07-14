Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Installing Slice 0.8 - Audit + Replay contracts (implementation-ready)..." -ForegroundColor Cyan

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Write-Utf8File {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $dir = Split-Path -Parent $Path
    if ($dir) {
        Ensure-Directory -Path $dir
    }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
    Write-Host "Wrote $Path" -ForegroundColor Green
}

Ensure-Directory "scripts"
Ensure-Directory "src/smart_money/core"
Ensure-Directory "tests"

$auditPy = @'
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .ids import deterministic_id
from .serialization import canonical_json


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
        raise TypeError(f"{field_name} must be Decimal or None, not float")

    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal or None")

    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")

    return value


def _validate_canonical_json_text(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("metadata_json must be a string")

    parsed = json.loads(value)
    canonical = canonical_json(parsed)
    if canonical != value:
        raise ValueError("metadata_json must already be canonical JSON text")
    return value


def _normalize_evidence_refs(value: tuple["EvidenceRef", ...], field_name: str) -> tuple["EvidenceRef", ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple")

    for item in value:
        if not isinstance(item, EvidenceRef):
            raise TypeError(f"{field_name} items must be EvidenceRef")

    return tuple(sorted(value, key=lambda item: canonical_json(item.canonical_dict())))


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
            object.__setattr__(self, "metadata_json", _validate_canonical_json_text(self.metadata_json))

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

        normalized_hits = tuple(sorted(self.hits, key=lambda item: canonical_json(item.canonical_dict())))
        normalized_rejects = tuple(sorted(self.rejects, key=lambda item: canonical_json(item.canonical_dict())))
        normalized_context_refs = _normalize_evidence_refs(self.context_refs, "context_refs")

        object.__setattr__(self, "hits", normalized_hits)
        object.__setattr__(self, "rejects", normalized_rejects)
        object.__setattr__(self, "context_refs", normalized_context_refs)

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
    if not isinstance(hits, tuple):
        raise TypeError("hits must be a tuple")
    if not isinstance(rejects, tuple):
        raise TypeError("rejects must be a tuple")

    for item in hits:
        if not isinstance(item, RuleHit):
            raise TypeError("hits items must be RuleHit")

    for item in rejects:
        if not isinstance(item, RejectReason):
            raise TypeError("rejects items must be RejectReason")

    normalized_hits = tuple(sorted(hits, key=lambda item: canonical_json(item.canonical_dict())))
    normalized_rejects = tuple(sorted(rejects, key=lambda item: canonical_json(item.canonical_dict())))
    normalized_context_refs = _normalize_evidence_refs(context_refs, "context_refs")

    payload = {
        "subject_id": _require_non_empty_text(subject_id, "subject_id"),
        "stage": _require_non_empty_text(stage, "stage"),
        "hits": tuple(item.canonical_dict() for item in normalized_hits),
        "rejects": tuple(item.canonical_dict() for item in normalized_rejects),
        "context_refs": tuple(item.canonical_dict() for item in normalized_context_refs),
    }

    trace_id = deterministic_id("decision_trace", payload)

    return DecisionTrace(
        trace_id=trace_id,
        subject_id=subject_id,
        stage=stage,
        hits=normalized_hits,
        rejects=normalized_rejects,
        context_refs=normalized_context_refs,
    )
'@

$replayPy = @'
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .ids import deterministic_id
from .time import ensure_utc_datetime


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


def _normalize_subject_ids(value: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError("subject_ids must be a tuple")

    normalized: list[str] = []
    for item in value:
        normalized.append(_require_non_empty_text(item, "subject_ids"))

    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True)
class ReplayManifest:
    manifest_id: str
    pipeline_version: str
    input_dataset_hash: str
    config_hash: str
    symbol: str | None = None
    venue: str | None = None
    timeframe: str | None = None
    range_start: datetime | None = None
    range_end: datetime | None = None
    subject_ids: tuple[str, ...] = ()
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "manifest_id", _require_non_empty_text(self.manifest_id, "manifest_id"))
        object.__setattr__(self, "pipeline_version", _require_non_empty_text(self.pipeline_version, "pipeline_version"))
        object.__setattr__(self, "input_dataset_hash", _require_non_empty_text(self.input_dataset_hash, "input_dataset_hash"))
        object.__setattr__(self, "config_hash", _require_non_empty_text(self.config_hash, "config_hash"))

        object.__setattr__(self, "symbol", _require_optional_text(self.symbol, "symbol"))
        object.__setattr__(self, "venue", _require_optional_text(self.venue, "venue"))
        object.__setattr__(self, "timeframe", _require_optional_text(self.timeframe, "timeframe"))
        object.__setattr__(self, "notes", _require_optional_text(self.notes, "notes"))

        if self.range_start is not None:
            object.__setattr__(self, "range_start", ensure_utc_datetime(self.range_start))
        if self.range_end is not None:
            object.__setattr__(self, "range_end", ensure_utc_datetime(self.range_end))

        if self.range_start is not None and self.range_end is not None:
            if self.range_start > self.range_end:
                raise ValueError("range_start must be less than or equal to range_end")

        object.__setattr__(self, "subject_ids", _normalize_subject_ids(self.subject_ids))

        expected_manifest_id = deterministic_id("replay_manifest", self.identity_payload())
        if self.manifest_id != expected_manifest_id:
            raise ValueError("manifest_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "pipeline_version": self.pipeline_version,
            "input_dataset_hash": self.input_dataset_hash,
            "config_hash": self.config_hash,
            "symbol": self.symbol,
            "venue": self.venue,
            "timeframe": self.timeframe,
            "range_start": self.range_start,
            "range_end": self.range_end,
            "subject_ids": self.subject_ids,
            "notes": self.notes,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            **self.identity_payload(),
        }


def make_replay_manifest(
    *,
    pipeline_version: str,
    input_dataset_hash: str,
    config_hash: str,
    symbol: str | None = None,
    venue: str | None = None,
    timeframe: str | None = None,
    range_start: datetime | None = None,
    range_end: datetime | None = None,
    subject_ids: tuple[str, ...] = (),
    notes: str | None = None,
) -> ReplayManifest:
    normalized_range_start = ensure_utc_datetime(range_start) if range_start is not None else None
    normalized_range_end = ensure_utc_datetime(range_end) if range_end is not None else None

    if normalized_range_start is not None and normalized_range_end is not None:
        if normalized_range_start > normalized_range_end:
            raise ValueError("range_start must be less than or equal to range_end")

    payload = {
        "pipeline_version": _require_non_empty_text(pipeline_version, "pipeline_version"),
        "input_dataset_hash": _require_non_empty_text(input_dataset_hash, "input_dataset_hash"),
        "config_hash": _require_non_empty_text(config_hash, "config_hash"),
        "symbol": _require_optional_text(symbol, "symbol"),
        "venue": _require_optional_text(venue, "venue"),
        "timeframe": _require_optional_text(timeframe, "timeframe"),
        "range_start": normalized_range_start,
        "range_end": normalized_range_end,
        "subject_ids": _normalize_subject_ids(subject_ids),
        "notes": _require_optional_text(notes, "notes"),
    }

    manifest_id = deterministic_id("replay_manifest", payload)

    return ReplayManifest(
        manifest_id=manifest_id,
        pipeline_version=pipeline_version,
        input_dataset_hash=input_dataset_hash,
        config_hash=config_hash,
        symbol=symbol,
        venue=venue,
        timeframe=timeframe,
        range_start=range_start,
        range_end=range_end,
        subject_ids=subject_ids,
        notes=notes,
    )
'@

$coreInitPy = @'
"""Pure deterministic core for Smart Money market-structure analysis."""

from .audit import DecisionTrace, EvidenceRef, RejectReason, RuleHit, make_decision_trace
from .replay import ReplayManifest, make_replay_manifest

__all__ = [
    "DecisionTrace",
    "EvidenceRef",
    "RejectReason",
    "ReplayManifest",
    "RuleHit",
    "make_decision_trace",
    "make_replay_manifest",
]
'@

$testAuditPy = @'
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


def test_evidence_ref_metadata_json_must_already_be_canonical() -> None:
    with pytest.raises(ValueError, match="canonical JSON"):
        EvidenceRef(
            kind="candle",
            ref_id="candle_001",
            metadata_json='{"b":2,"a":1}',
        )


def test_rejectreason_and_rulehit_default_evidence_is_empty_tuple() -> None:
    reject = RejectReason(code="reject.a", message="message-a")
    hit = RuleHit(rule_code="rule.a", summary="summary-a")

    assert reject.evidence == ()
    assert hit.evidence == ()
    assert isinstance(reject.evidence, tuple)
    assert isinstance(hit.evidence, tuple)


def test_rulehit_rejects_float_score() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        RuleHit(
            rule_code="rule.a",
            summary="summary-a",
            score=1.25,  # type: ignore[arg-type]
        )


def test_rulehit_accepts_decimal_score() -> None:
    hit = RuleHit(
        rule_code="rule.a",
        summary="summary-a",
        score=Decimal("1.25"),
    )

    assert hit.score == Decimal("1.25")


def test_decision_trace_trace_id_is_stable_for_same_semantic_payload() -> None:
    hit_1 = RuleHit(
        rule_code="rule.a",
        summary="summary-a",
        evidence=(_evidence_b(), _evidence_a()),
        score=Decimal("1.00"),
    )
    reject_1 = RejectReason(
        code="reject.a",
        message="message-a",
        evidence=(_evidence_b(), _evidence_a()),
    )

    trace_1 = make_decision_trace(
        subject_id="subject_1",
        stage="decision",
        hits=(hit_1,),
        rejects=(reject_1,),
        context_refs=(_evidence_b(), _evidence_a()),
    )

    hit_2 = RuleHit(
        rule_code="rule.a",
        summary="summary-a",
        evidence=(_evidence_a(), _evidence_b()),
        score=Decimal("1.00"),
    )
    reject_2 = RejectReason(
        code="reject.a",
        message="message-a",
        evidence=(_evidence_a(), _evidence_b()),
    )

    trace_2 = make_decision_trace(
        subject_id="subject_1",
        stage="decision",
        hits=(hit_2,),
        rejects=(reject_2,),
        context_refs=(_evidence_a(), _evidence_b()),
    )

    assert trace_1.trace_id == trace_2.trace_id


def test_decision_trace_trace_id_changes_when_content_changes() -> None:
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


def test_manual_wrong_trace_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="trace_id"):
        DecisionTrace(
            trace_id="decision_trace_wrong",
            subject_id="subject_1",
            stage="decision",
        )


def test_decision_trace_is_frozen() -> None:
    trace = make_decision_trace(subject_id="subject_1", stage="decision")

    with pytest.raises(FrozenInstanceError):
        trace.stage = "setup"  # type: ignore[misc]


def test_audit_contracts_are_canonical_json_compatible() -> None:
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
'@

$testReplayPy = @'
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from smart_money.core.replay import ReplayManifest, make_replay_manifest
from smart_money.core.serialization import canonical_json


def test_replay_manifest_manifest_id_is_stable() -> None:
    first = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
        symbol="SOLUSDT",
        venue="base",
        timeframe="5m",
        subject_ids=("b", "a"),
        notes="stable-note",
    )
    second = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
        symbol="SOLUSDT",
        venue="base",
        timeframe="5m",
        subject_ids=("a", "b"),
        notes="stable-note",
    )

    assert first.manifest_id == second.manifest_id


def test_replay_manifest_manifest_id_changes_when_input_dataset_hash_changes() -> None:
    first = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
    )
    second = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_002",
        config_hash="config_hash_001",
    )

    assert first.manifest_id != second.manifest_id


def test_replay_manifest_manifest_id_changes_when_config_hash_changes() -> None:
    first = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
    )
    second = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_002",
    )

    assert first.manifest_id != second.manifest_id


def test_replay_manifest_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        make_replay_manifest(
            pipeline_version="pipeline.v1",
            input_dataset_hash="dataset_hash_001",
            config_hash="config_hash_001",
            range_start=datetime(2024, 1, 1, 0, 0),
        )


def test_replay_manifest_accepts_and_normalizes_aware_datetime_to_utc() -> None:
    manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
        range_start=datetime(2024, 1, 1, 3, 30, tzinfo=timezone(timedelta(hours=3, minutes=30))),
        range_end=datetime(2024, 1, 1, 4, 30, tzinfo=timezone(timedelta(hours=3, minutes=30))),
    )

    assert manifest.range_start == datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert manifest.range_end == datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc)


def test_replay_manifest_manual_wrong_manifest_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="manifest_id"):
        ReplayManifest(
            manifest_id="replay_manifest_wrong",
            pipeline_version="pipeline.v1",
            input_dataset_hash="dataset_hash_001",
            config_hash="config_hash_001",
        )


def test_replay_manifest_is_frozen() -> None:
    manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
    )

    with pytest.raises(FrozenInstanceError):
        manifest.symbol = "BTCUSDT"  # type: ignore[misc]


def test_replay_manifest_is_canonical_json_compatible() -> None:
    manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
        symbol="SOLUSDT",
        venue="base",
        timeframe="5m",
        subject_ids=("subject_b", "subject_a"),
        notes="stable-note",
    )

    first = canonical_json(manifest.canonical_dict())
    second = canonical_json(manifest.canonical_dict())

    assert first == second
'@

Write-Utf8File "src/smart_money/core/audit.py" $auditPy
Write-Utf8File "src/smart_money/core/replay.py" $replayPy
Write-Utf8File "src/smart_money/core/__init__.py" $coreInitPy
Write-Utf8File "tests/test_audit_contracts.py" $testAuditPy
Write-Utf8File "tests/test_replay_manifest.py" $testReplayPy

Write-Host ""
Write-Host "Slice 0.8 installation complete." -ForegroundColor Cyan
Write-Host "Files updated:" -ForegroundColor Yellow
Write-Host "  - src/smart_money/core/audit.py"
Write-Host "  - src/smart_money/core/replay.py"
Write-Host "  - src/smart_money/core/__init__.py"
Write-Host "  - tests/test_audit_contracts.py"
Write-Host "  - tests/test_replay_manifest.py"
