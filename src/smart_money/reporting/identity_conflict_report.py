from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id
from smart_money.domain.identity_evidence import (
    IdentityEvidence,
    IdentityEvidenceStatus,
)

_SCHEMA_VERSION = "identity_conflict_report.v1"


@dataclass(frozen=True, slots=True)
class IdentityConflictReport:
    """Deterministic, evidence-only report for one identity conflict."""

    evidence_id: str
    subject: str
    subject_kind: str
    source_id: str
    conflict_code: str
    left: str
    right: str
    blocking: bool
    provenance: dict[str, str]
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "evidence_id",
            "subject",
            "subject_kind",
            "source_id",
            "conflict_code",
            "left",
            "right",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.subject_kind not in {"wallet", "token", "pool"}:
            raise ValueError("unsupported subject_kind")
        if not isinstance(self.blocking, bool):
            raise TypeError("blocking must be a boolean")
        if not isinstance(self.provenance, dict) or not self.provenance:
            raise ValueError("provenance must be a non-empty mapping")
        if not all(
            isinstance(key, str)
            and key.strip()
            and isinstance(value, str)
            and value.strip()
            for key, value in self.provenance.items()
        ):
            raise ValueError("provenance must contain non-empty text")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported identity conflict report schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "blocking": self.blocking,
            "conflict_code": self.conflict_code,
            "evidence_id": self.evidence_id,
            "left": self.left,
            "provenance": dict(sorted(self.provenance.items())),
            "right": self.right,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "subject": self.subject,
            "subject_kind": self.subject_kind,
        }

    @property
    def report_id(self) -> str:
        return deterministic_id("identity-conflict-report", self.canonical_dict())


def render_identity_conflict_report(
    evidence: IdentityEvidence,
) -> IdentityConflictReport:
    """Project explicit identity conflict evidence without promoting it to truth."""
    if not isinstance(evidence, IdentityEvidence):
        raise TypeError("evidence must be an IdentityEvidence")
    if evidence.status is not IdentityEvidenceStatus.CONFLICT:
        raise ValueError("identity conflict report requires CONFLICT evidence")
    conflict = evidence.conflict
    if conflict is None:
        raise ValueError("CONFLICT evidence is missing conflict details")
    return IdentityConflictReport(
        evidence_id=evidence.evidence_id,
        subject=evidence.subject.strip(),
        subject_kind=evidence.subject_kind,
        source_id=evidence.source_id.strip(),
        conflict_code=conflict.code,
        left=conflict.left,
        right=conflict.right,
        blocking=conflict.blocking,
        provenance=dict(sorted(evidence.provenance.items())),
    )


__all__ = ["IdentityConflictReport", "render_identity_conflict_report"]
