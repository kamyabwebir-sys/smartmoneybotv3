from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.wallet_candidate_evidence import (
    WalletCandidateEvidence,
    WalletCandidateEvidenceStatus,
)
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "wallet_candidate_evidence_store.v1"


class JsonWalletCandidateEvidenceStore:
    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._evidence: dict[str, WalletCandidateEvidence] = {}
        self._load_existing()

    def append(self, evidence: WalletCandidateEvidence) -> str:
        if not isinstance(evidence, WalletCandidateEvidence):
            raise TypeError("evidence must be WalletCandidateEvidence")
        existing = self._evidence.get(evidence.evidence_id)
        if existing is not None:
            if existing != evidence:
                raise RuntimeError("wallet candidate evidence identity collision")
            return evidence.evidence_id
        candidate = dict(self._evidence)
        candidate[evidence.evidence_id] = evidence
        self._persist(tuple(candidate.values()))
        self._evidence = candidate
        return evidence.evidence_id

    def get(self, evidence_id: str) -> WalletCandidateEvidence | None:
        return self._evidence.get(evidence_id)

    def iter_evidence(self) -> Iterator[WalletCandidateEvidence]:
        return iter(tuple(self._evidence.values()))

    @property
    def evidence_count(self) -> int:
        return len(self._evidence)

    def _load_existing(self) -> None:
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        source = self._file_path if self._file_path.is_file() else temporary
        if not source.is_file():
            return
        loaded = self._load_path(source)
        if source == temporary:
            atomic_replace(temporary, self._file_path)
        self._evidence = loaded

    def _load_path(self, path: Path) -> dict[str, WalletCandidateEvidence]:
        raw = path.read_text(encoding="utf-8")
        document = json.loads(raw)
        if not isinstance(document, dict) or document.get("schema_version") != _SCHEMA_VERSION:
            raise ValueError("invalid wallet candidate evidence store schema")
        records = document.get("evidence")
        if not isinstance(records, list) or document.get("content_hash") != _hash(records):
            raise ValueError("wallet candidate evidence store content hash mismatch")
        if canonical_json(document) != raw:
            raise ValueError("wallet candidate evidence store is not canonical JSON")
        loaded: dict[str, WalletCandidateEvidence] = {}
        for record in records:
            feature_data = record["feature"]
            feature_identity = {
                key: feature_data[key]
                for key in (
                    "activity_count",
                    "buy_ratio_bps",
                    "cohort_count",
                    "data_completeness_bps",
                    "early_entry_consistency_bps",
                    "profile_id",
                    "relationship_count",
                    "schema_version",
                    "wallet",
                )
            }
            feature = WalletCandidateFeature(
                **feature_identity,
                feature_id=feature_data["feature_id"],
            )
            evidence = WalletCandidateEvidence(
                evidence_id=record["evidence_id"],
                feature=feature,
                provenance=record["provenance"],
                reason_codes=tuple(record["reason_codes"]),
                schema_version=record["schema_version"],
                status=WalletCandidateEvidenceStatus(record["status"]),
            )
            if evidence.evidence_id in loaded:
                raise ValueError("duplicate wallet candidate evidence")
            loaded[evidence.evidence_id] = evidence
        return loaded

    def _persist(self, evidence: tuple[WalletCandidateEvidence, ...]) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        records = [item.canonical_dict() for item in evidence]
        document = {
            "content_hash": _hash(records),
            "evidence": records,
            "schema_version": _SCHEMA_VERSION,
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


def _hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = ["JsonWalletCandidateEvidenceStore"]
