from __future__ import annotations

import hmac
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from smart_money.analytics.scoring import ScoreReport
from smart_money.application.replay_integrity import (
    ReplayIntegrityManifest,
    score_report_hash,
)
from smart_money.core.ids import deterministic_id
from smart_money.core.replay import ReplayManifest
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "score_evidence_trace.v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_VALID_STATUS_COMPONENTS = {
    "scored": frozenset({"bullish_count", "bearish_count"}),
    "zero_weight": frozenset({"neutral_count", "unknown_direction_count"}),
    "ignored": frozenset({"ignored_evidence_count"}),
}
_DIRECTION_CONTRIBUTIONS = {
    "bullish": ("scored", "bullish_count", Decimal("0.5")),
    "bearish": ("scored", "bearish_count", Decimal("-0.5")),
    "neutral": ("zero_weight", "neutral_count", Decimal("0")),
}
_COMPONENT_DELTAS = {
    "bullish_count": Decimal("0.5"),
    "bearish_count": Decimal("-0.5"),
    "neutral_count": Decimal("0"),
    "unknown_direction_count": Decimal("0"),
    "ignored_evidence_count": Decimal("0"),
}


def _require_non_empty_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _require_sha256(value: object, field_name: str) -> str:
    digest = _require_non_empty_text(value, field_name)
    if _SHA256_PATTERN.fullmatch(digest) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")
    return digest


@dataclass(frozen=True, slots=True)
class ScoreEvidenceContribution:
    """One canonical evidence reference and its deterministic score effect."""

    evidence_id: str
    source_id: str
    evidence_type: str
    timestamp: int
    status: str
    score_component: str
    score_delta: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_id",
            _require_non_empty_text(self.evidence_id, "evidence_id"),
        )
        object.__setattr__(
            self,
            "source_id",
            _require_non_empty_text(self.source_id, "source_id"),
        )
        object.__setattr__(
            self,
            "evidence_type",
            _require_non_empty_text(self.evidence_type, "evidence_type"),
        )
        object.__setattr__(
            self,
            "status",
            _require_non_empty_text(self.status, "status"),
        )
        object.__setattr__(
            self,
            "score_component",
            _require_non_empty_text(self.score_component, "score_component"),
        )
        if isinstance(self.timestamp, bool) or not isinstance(self.timestamp, int):
            raise TypeError("timestamp must be an integer")
        if not isinstance(self.score_delta, Decimal):
            raise TypeError("score_delta must be Decimal")
        if not self.score_delta.is_finite():
            raise ValueError("score_delta must be finite")

        valid_components = _VALID_STATUS_COMPONENTS.get(self.status)
        if (
            valid_components is None
            or self.score_component not in valid_components
        ):
            raise ValueError("status and score_component are inconsistent")
        if self.score_delta != _COMPONENT_DELTAS[self.score_component]:
            raise ValueError("score_delta does not match score_component")

    def canonical_dict(self) -> dict[str, str | int | Decimal]:
        return {
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "evidence_type": self.evidence_type,
            "timestamp": self.timestamp,
            "status": self.status,
            "score_component": self.score_component,
            "score_delta": self.score_delta,
        }


@dataclass(frozen=True, slots=True)
class ScoreEvidenceTrace:
    """Application-level chain from score output to canonical evidence."""

    trace_id: str
    ledger_content_hash: str
    replay_manifest_id: str
    integrity_id: str
    score_output_hash: str
    contributions: tuple[ScoreEvidenceContribution, ...]
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "trace_id",
            _require_non_empty_text(self.trace_id, "trace_id"),
        )
        object.__setattr__(
            self,
            "ledger_content_hash",
            _require_sha256(self.ledger_content_hash, "ledger_content_hash"),
        )
        object.__setattr__(
            self,
            "replay_manifest_id",
            _require_non_empty_text(
                self.replay_manifest_id,
                "replay_manifest_id",
            ),
        )
        object.__setattr__(
            self,
            "integrity_id",
            _require_non_empty_text(self.integrity_id, "integrity_id"),
        )
        object.__setattr__(
            self,
            "score_output_hash",
            _require_sha256(self.score_output_hash, "score_output_hash"),
        )
        object.__setattr__(
            self,
            "schema_version",
            _require_non_empty_text(self.schema_version, "schema_version"),
        )
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(
                f"unsupported score evidence trace schema_version: {self.schema_version}"
            )
        if not isinstance(self.contributions, tuple):
            raise TypeError("contributions must be a tuple")
        if not all(
            isinstance(item, ScoreEvidenceContribution)
            for item in self.contributions
        ):
            raise TypeError(
                "contributions items must be ScoreEvidenceContribution"
            )

        ordered = tuple(sorted(self.contributions, key=lambda item: item.evidence_id))
        if len({item.evidence_id for item in ordered}) != len(ordered):
            raise ValueError("duplicate evidence_id values are not allowed")
        object.__setattr__(self, "contributions", ordered)

        expected_id = deterministic_id("score_evidence_trace", self.identity_payload())
        if self.trace_id != expected_id:
            raise ValueError("trace_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ledger_content_hash": self.ledger_content_hash,
            "replay_manifest_id": self.replay_manifest_id,
            "integrity_id": self.integrity_id,
            "score_output_hash": self.score_output_hash,
            "contributions": tuple(
                item.canonical_dict() for item in self.contributions
            ),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"trace_id": self.trace_id, **self.identity_payload()}


def _contribution_for(payload: EvidencePayload) -> ScoreEvidenceContribution:
    if not payload.source_id.strip():
        raise ValueError("evidence source_id must be non-empty for traceability")
    if not payload.evidence_type.strip():
        raise ValueError("evidence_type must be non-empty for traceability")

    if payload.evidence_type != "market_structure":
        status, component, delta = (
            "ignored",
            "ignored_evidence_count",
            Decimal("0"),
        )
    else:
        direction = payload.data.get("direction", "neutral")
        normalized_direction = (
            direction.strip().lower() if isinstance(direction, str) else ""
        )
        status, component, delta = _DIRECTION_CONTRIBUTIONS.get(
            normalized_direction,
            ("zero_weight", "unknown_direction_count", Decimal("0")),
        )

    return ScoreEvidenceContribution(
        evidence_id=payload.get_canonical_id(),
        source_id=payload.source_id,
        evidence_type=payload.evidence_type,
        timestamp=payload.timestamp,
        status=status,
        score_component=component,
        score_delta=delta,
    )


def _validate_breakdown(
    report: ScoreReport,
    contributions: tuple[ScoreEvidenceContribution, ...],
) -> None:
    component_counts = {
        component: sum(
            item.score_component == component for item in contributions
        )
        for component in (
            "bullish_count",
            "bearish_count",
            "neutral_count",
            "unknown_direction_count",
            "ignored_evidence_count",
        )
    }
    structure_count = len(contributions) - component_counts["ignored_evidence_count"]
    expected_values: dict[str, int | Decimal] = {
        **component_counts,
        "evidence_count": len(contributions),
        "structure_count": structure_count,
        "raw_score": sum(
            (item.score_delta for item in contributions),
            start=Decimal("0"),
        ),
    }
    expected_values["bounded_score"] = max(
        Decimal("-1"),
        min(expected_values["raw_score"], Decimal("1")),
    )
    for field, expected in expected_values.items():
        if report.score_breakdown.get(field) != expected:
            raise ValueError(f"score breakdown does not match evidence trace: {field}")
    if report.score != expected_values["bounded_score"]:
        raise ValueError("score does not match evidence trace contributions")


def create_score_evidence_trace(
    *,
    evidence: tuple[EvidencePayload, ...],
    report: ScoreReport,
    replay_manifest: ReplayManifest,
    integrity: ReplayIntegrityManifest,
    ledger_content_hash: str,
) -> ScoreEvidenceTrace:
    """Bind every score component to canonical evidence and replay identities."""
    if not isinstance(evidence, tuple):
        raise TypeError("evidence must be a tuple")
    if not all(isinstance(item, EvidencePayload) for item in evidence):
        raise TypeError("evidence items must be EvidencePayload")
    if not isinstance(report, ScoreReport):
        raise TypeError("report must be a ScoreReport")
    if not isinstance(replay_manifest, ReplayManifest):
        raise TypeError("replay_manifest must be a ReplayManifest")
    if not isinstance(integrity, ReplayIntegrityManifest):
        raise TypeError("integrity must be a ReplayIntegrityManifest")

    ledger_hash = _require_sha256(ledger_content_hash, "ledger_content_hash")
    if not hmac.compare_digest(ledger_hash, integrity.input_hash):
        raise ValueError("ledger hash does not match replay integrity")
    if replay_manifest.manifest_id != integrity.replay_manifest_id:
        raise ValueError("replay manifest does not match replay integrity")
    if replay_manifest.input_dataset_hash != ledger_hash:
        raise ValueError("replay manifest does not match ledger hash")
    if report.evidence_count != len(evidence):
        raise ValueError("report evidence_count does not match evidence")
    if integrity.evidence_count != len(evidence):
        raise ValueError("integrity evidence_count does not match evidence")
    if not hmac.compare_digest(score_report_hash(report), integrity.output_hash):
        raise ValueError("report does not match replay integrity output hash")

    contributions = tuple(_contribution_for(item) for item in evidence)
    _validate_breakdown(report, contributions)
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "ledger_content_hash": ledger_hash,
        "replay_manifest_id": replay_manifest.manifest_id,
        "integrity_id": integrity.integrity_id,
        "score_output_hash": integrity.output_hash,
        "contributions": tuple(
            item.canonical_dict()
            for item in sorted(contributions, key=lambda item: item.evidence_id)
        ),
    }
    return ScoreEvidenceTrace(
        trace_id=deterministic_id("score_evidence_trace", payload),
        ledger_content_hash=ledger_hash,
        replay_manifest_id=replay_manifest.manifest_id,
        integrity_id=integrity.integrity_id,
        score_output_hash=integrity.output_hash,
        contributions=contributions,
    )


__all__ = [
    "ScoreEvidenceContribution",
    "ScoreEvidenceTrace",
    "create_score_evidence_trace",
]
