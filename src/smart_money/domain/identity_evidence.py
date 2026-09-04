from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from smart_money.core.ids import deterministic_id
from smart_money.domain.chain_identity import IdentityConflict


class IdentityEvidenceStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    PROPOSED = "PROPOSED"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class IdentityEvidence:
    subject: str
    subject_kind: str
    status: IdentityEvidenceStatus
    source_id: str
    provenance: Mapping[str, str]
    conflict: IdentityConflict | None = None
    schema_version: str = "identity_evidence.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.subject, str) or not self.subject.strip():
            raise ValueError("subject must be a non-empty string")
        if self.subject_kind not in {"wallet", "token", "pool"}:
            raise ValueError("unsupported subject_kind")
        if not isinstance(self.status, IdentityEvidenceStatus):
            raise TypeError("status must be IdentityEvidenceStatus")
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be a non-empty string")
        if not isinstance(self.provenance, Mapping) or not self.provenance:
            raise ValueError("provenance must be a non-empty mapping")
        if not all(
            isinstance(key, str) and key.strip()
            and isinstance(value, str) and value.strip()
            for key, value in self.provenance.items()
        ):
            raise ValueError("provenance must contain non-empty text")
        if self.status is IdentityEvidenceStatus.CONFLICT and self.conflict is None:
            raise ValueError("CONFLICT status requires conflict evidence")
        if self.status is not IdentityEvidenceStatus.CONFLICT and self.conflict is not None:
            raise ValueError("non-CONFLICT status cannot contain conflict evidence")
        if self.schema_version != "identity_evidence.v1":
            raise ValueError("unsupported identity evidence schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "conflict": None
            if self.conflict is None
            else {
                "blocking": self.conflict.blocking,
                "code": self.conflict.code,
                "left": self.conflict.left,
                "right": self.conflict.right,
            },
            "provenance": dict(sorted(self.provenance.items())),
            "schema_version": self.schema_version,
            "source_id": self.source_id.strip(),
            "status": self.status.value,
            "subject": self.subject.strip(),
            "subject_kind": self.subject_kind,
        }

    @property
    def evidence_id(self) -> str:
        return deterministic_id("identity-evidence", self.canonical_dict())

__all__ = ["IdentityEvidence", "IdentityEvidenceStatus"]
