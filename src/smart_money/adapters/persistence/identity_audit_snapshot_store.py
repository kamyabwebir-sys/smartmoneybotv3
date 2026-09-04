from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.core.serialization import canonical_json
from smart_money.domain.identity_evidence import IdentityEvidence

_SCHEMA_VERSION = "identity_audit_snapshot.v1"


def _content_hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class IdentityAuditSnapshot:
    evidence_id: str
    subject: str
    subject_kind: str
    source_id: str
    status: str
    evidence: dict[str, Any]
    content_hash: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "evidence_id",
            "subject",
            "subject_kind",
            "source_id",
            "status",
            "content_hash",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.evidence, dict) or not self.evidence:
            raise ValueError("evidence must be a non-empty mapping")
        if len(self.content_hash) != 64 or any(
            character not in "0123456789abcdef" for character in self.content_hash
        ):
            raise ValueError("content_hash must be lowercase SHA-256 hex")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported identity audit snapshot schema_version")
        if not hmac.compare_digest(self.content_hash, _content_hash(self.evidence)):
            raise ValueError("identity audit snapshot content hash mismatch")
        if self.evidence.get("evidence_id") != self.evidence_id:
            raise ValueError("identity audit snapshot evidence identity mismatch")

    @classmethod
    def from_evidence(cls, evidence: IdentityEvidence) -> IdentityAuditSnapshot:
        if not isinstance(evidence, IdentityEvidence):
            raise TypeError("evidence must be an IdentityEvidence")
        canonical = evidence.canonical_dict()
        canonical["evidence_id"] = evidence.evidence_id
        return cls(
            evidence_id=evidence.evidence_id,
            subject=evidence.subject,
            subject_kind=evidence.subject_kind,
            source_id=evidence.source_id,
            status=evidence.status.value,
            evidence=canonical,
            content_hash=_content_hash(canonical),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "content_hash": self.content_hash,
            "evidence": self.evidence,
            "evidence_id": self.evidence_id,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "status": self.status,
            "subject": self.subject,
            "subject_kind": self.subject_kind,
        }


@dataclass(frozen=True, slots=True)
class IdentityAuditReplayReceipt:
    snapshot_id: str
    evidence_id: str
    content_hash: str
    matches: bool
    schema_version: str = "identity_audit_replay.v1"

    def __post_init__(self) -> None:
        for name in ("snapshot_id", "evidence_id", "content_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(self.content_hash) != 64:
            raise ValueError("content_hash must be a SHA-256 hex digest")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if self.schema_version != "identity_audit_replay.v1":
            raise ValueError("unsupported identity audit replay schema_version")


class JsonIdentityAuditSnapshotStore:
    """Atomic persistence for one canonical identity audit snapshot."""

    def save(
        self,
        evidence: IdentityEvidence,
        file_path: str | os.PathLike[str],
    ) -> IdentityAuditSnapshot:
        snapshot = IdentityAuditSnapshot.from_evidence(evidence)
        path = Path(file_path)
        if path.parent != Path("."):
            path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(snapshot.canonical_dict()))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, path)
        return snapshot

    def load(self, file_path: str | os.PathLike[str]) -> IdentityAuditSnapshot:
        path = Path(file_path)
        try:
            raw = path.read_text(encoding="utf-8")
            document: Any = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("identity audit snapshot is not valid JSON") from exc
        if not isinstance(document, dict) or set(document) != {
            "content_hash",
            "evidence",
            "evidence_id",
            "schema_version",
            "source_id",
            "status",
            "subject",
            "subject_kind",
        }:
            raise ValueError("identity audit snapshot keys do not match schema")
        snapshot = IdentityAuditSnapshot(
            evidence_id=document["evidence_id"],
            subject=document["subject"],
            subject_kind=document["subject_kind"],
            source_id=document["source_id"],
            status=document["status"],
            evidence=document["evidence"],
            content_hash=document["content_hash"],
            schema_version=document["schema_version"],
        )
        if canonical_json(snapshot.canonical_dict()) != raw:
            raise ValueError("identity audit snapshot is not canonical JSON")
        return snapshot

    def replay(
        self,
        evidence: IdentityEvidence,
        snapshot: IdentityAuditSnapshot,
    ) -> IdentityAuditReplayReceipt:
        if not isinstance(evidence, IdentityEvidence):
            raise TypeError("evidence must be an IdentityEvidence")
        if not isinstance(snapshot, IdentityAuditSnapshot):
            raise TypeError("snapshot must be an IdentityAuditSnapshot")
        expected = IdentityAuditSnapshot.from_evidence(evidence)
        matches = (
            expected.evidence_id == snapshot.evidence_id
            and expected.subject == snapshot.subject
            and expected.subject_kind == snapshot.subject_kind
            and expected.source_id == snapshot.source_id
            and expected.status == snapshot.status
            and hmac.compare_digest(expected.content_hash, snapshot.content_hash)
            and expected.evidence == snapshot.evidence
        )
        if not matches:
            raise ValueError("identity audit replay does not match snapshot")
        return IdentityAuditReplayReceipt(
            snapshot_id=_content_hash(snapshot.canonical_dict()),
            evidence_id=evidence.evidence_id,
            content_hash=snapshot.content_hash,
            matches=True,
        )


__all__ = [
    "IdentityAuditReplayReceipt",
    "IdentityAuditSnapshot",
    "JsonIdentityAuditSnapshotStore",
]
