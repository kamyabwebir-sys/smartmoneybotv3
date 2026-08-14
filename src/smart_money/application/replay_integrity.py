from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from typing import Any

from smart_money.analytics.scoring import ScoreReport
from smart_money.core.ids import deterministic_id
from smart_money.core.replay import ReplayManifest
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "replay_integrity.v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_COMPARABLE_FIELDS = (
    "schema_version",
    "replay_manifest_id",
    "pipeline_version",
    "config_hash",
    "input_hash",
    "output_hash",
    "evidence_count",
)


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


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def score_report_hash(report: ScoreReport) -> str:
    """Hash the complete canonical analytical output."""
    if not isinstance(report, ScoreReport):
        raise TypeError("report must be a ScoreReport")
    return _canonical_sha256(
        {
            "score": report.score,
            "reasoning": report.reasoning,
            "evidence_count": report.evidence_count,
            "score_breakdown": report.score_breakdown,
        }
    )


@dataclass(frozen=True, slots=True)
class ReplayIntegrityManifest:
    """Content-addressed receipt for one deterministic replay result."""

    integrity_id: str
    replay_manifest_id: str
    pipeline_version: str
    config_hash: str
    input_hash: str
    output_hash: str
    evidence_count: int
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "integrity_id",
            _require_non_empty_text(self.integrity_id, "integrity_id"),
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
            "pipeline_version",
            _require_non_empty_text(self.pipeline_version, "pipeline_version"),
        )
        object.__setattr__(
            self,
            "config_hash",
            _require_non_empty_text(self.config_hash, "config_hash"),
        )
        object.__setattr__(
            self,
            "input_hash",
            _require_sha256(self.input_hash, "input_hash"),
        )
        object.__setattr__(
            self,
            "output_hash",
            _require_sha256(self.output_hash, "output_hash"),
        )
        object.__setattr__(
            self,
            "schema_version",
            _require_non_empty_text(self.schema_version, "schema_version"),
        )

        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(
                f"unsupported replay integrity schema_version: {self.schema_version}"
            )
        if isinstance(self.evidence_count, bool) or not isinstance(
            self.evidence_count,
            int,
        ):
            raise TypeError("evidence_count must be an integer")
        if self.evidence_count < 0:
            raise ValueError("evidence_count must be non-negative")

        expected_id = deterministic_id(
            "replay_integrity",
            self.identity_payload(),
        )
        if self.integrity_id != expected_id:
            raise ValueError("integrity_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, str | int]:
        return {
            "schema_version": self.schema_version,
            "replay_manifest_id": self.replay_manifest_id,
            "pipeline_version": self.pipeline_version,
            "config_hash": self.config_hash,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "evidence_count": self.evidence_count,
        }

    def canonical_dict(self) -> dict[str, str | int]:
        return {
            "integrity_id": self.integrity_id,
            **self.identity_payload(),
        }


@dataclass(frozen=True, slots=True)
class ReplayIntegrityComparison:
    """Deterministic, audit-ready comparison of two replay receipts."""

    comparison_id: str
    expected_integrity_id: str
    actual_integrity_id: str
    matches: bool
    mismatch_fields: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "comparison_id",
            _require_non_empty_text(self.comparison_id, "comparison_id"),
        )
        object.__setattr__(
            self,
            "expected_integrity_id",
            _require_non_empty_text(
                self.expected_integrity_id,
                "expected_integrity_id",
            ),
        )
        object.__setattr__(
            self,
            "actual_integrity_id",
            _require_non_empty_text(
                self.actual_integrity_id,
                "actual_integrity_id",
            ),
        )
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if not isinstance(self.mismatch_fields, tuple):
            raise TypeError("mismatch_fields must be a tuple")

        normalized_fields = tuple(
            sorted(
                {
                    _require_non_empty_text(field, "mismatch_fields")
                    for field in self.mismatch_fields
                }
            )
        )
        object.__setattr__(self, "mismatch_fields", normalized_fields)
        if self.matches != (not normalized_fields):
            raise ValueError("matches must agree with mismatch_fields")

        expected_id = deterministic_id(
            "replay_integrity_comparison",
            self.identity_payload(),
        )
        if self.comparison_id != expected_id:
            raise ValueError("comparison_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, str | bool | tuple[str, ...]]:
        return {
            "expected_integrity_id": self.expected_integrity_id,
            "actual_integrity_id": self.actual_integrity_id,
            "matches": self.matches,
            "mismatch_fields": self.mismatch_fields,
        }

    def canonical_dict(self) -> dict[str, str | bool | tuple[str, ...]]:
        return {
            "comparison_id": self.comparison_id,
            **self.identity_payload(),
        }


class ReplayIntegrityError(RuntimeError):
    """Raised when replay integrity verification detects any mismatch."""

    def __init__(self, comparison: ReplayIntegrityComparison) -> None:
        self.comparison = comparison
        mismatches = ", ".join(comparison.mismatch_fields)
        super().__init__(f"replay integrity mismatch: {mismatches}")


def create_replay_integrity_manifest(
    *,
    replay_manifest: ReplayManifest,
    ledger_content_hash: str,
    report: ScoreReport,
) -> ReplayIntegrityManifest:
    """Create a receipt only when the declared and actual ledger hashes agree."""
    if not isinstance(replay_manifest, ReplayManifest):
        raise TypeError("replay_manifest must be a ReplayManifest")

    input_hash = _require_sha256(ledger_content_hash, "ledger_content_hash")
    declared_hash = _require_sha256(
        replay_manifest.input_dataset_hash,
        "replay_manifest.input_dataset_hash",
    )
    if not hmac.compare_digest(input_hash, declared_hash):
        raise ValueError(
            "ledger_content_hash does not match replay manifest input_dataset_hash"
        )

    payload: dict[str, str | int] = {
        "schema_version": _SCHEMA_VERSION,
        "replay_manifest_id": replay_manifest.manifest_id,
        "pipeline_version": replay_manifest.pipeline_version,
        "config_hash": replay_manifest.config_hash,
        "input_hash": input_hash,
        "output_hash": score_report_hash(report),
        "evidence_count": report.evidence_count,
    }
    return ReplayIntegrityManifest(
        integrity_id=deterministic_id("replay_integrity", payload),
        replay_manifest_id=replay_manifest.manifest_id,
        pipeline_version=replay_manifest.pipeline_version,
        config_hash=replay_manifest.config_hash,
        input_hash=input_hash,
        output_hash=payload["output_hash"],
        evidence_count=report.evidence_count,
    )


def compare_replay_integrity(
    expected: ReplayIntegrityManifest,
    actual: ReplayIntegrityManifest,
) -> ReplayIntegrityComparison:
    if not isinstance(expected, ReplayIntegrityManifest):
        raise TypeError("expected must be a ReplayIntegrityManifest")
    if not isinstance(actual, ReplayIntegrityManifest):
        raise TypeError("actual must be a ReplayIntegrityManifest")

    mismatch_fields = tuple(
        field
        for field in _COMPARABLE_FIELDS
        if getattr(expected, field) != getattr(actual, field)
    )
    payload: dict[str, str | bool | tuple[str, ...]] = {
        "expected_integrity_id": expected.integrity_id,
        "actual_integrity_id": actual.integrity_id,
        "matches": not mismatch_fields,
        "mismatch_fields": tuple(sorted(mismatch_fields)),
    }
    return ReplayIntegrityComparison(
        comparison_id=deterministic_id("replay_integrity_comparison", payload),
        expected_integrity_id=expected.integrity_id,
        actual_integrity_id=actual.integrity_id,
        matches=not mismatch_fields,
        mismatch_fields=mismatch_fields,
    )


def verify_replay_integrity(
    expected: ReplayIntegrityManifest,
    actual: ReplayIntegrityManifest,
) -> ReplayIntegrityComparison:
    """Return the comparison or fail closed with the same deterministic report."""
    comparison = compare_replay_integrity(expected, actual)
    if not comparison.matches:
        raise ReplayIntegrityError(comparison)
    return comparison


__all__ = [
    "ReplayIntegrityComparison",
    "ReplayIntegrityError",
    "ReplayIntegrityManifest",
    "compare_replay_integrity",
    "create_replay_integrity_manifest",
    "score_report_hash",
    "verify_replay_integrity",
]
