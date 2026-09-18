from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.audit_recovery_gate import (
    AuditRecoveryGateDecision,
    AuditRecoveryGateStatus,
)
from smart_money.application.checkpointed_ingestion import (
    CheckpointedIngestionResult,
)
from smart_money.application.recovery_gated_ingestion import (
    RecoveryGatedIngestionResult,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "recovery_gated_run_store.v1"
_DOCUMENT_KEYS = frozenset({"schema_version", "content_hash", "results"})
_RESULT_KEYS = frozenset(
    {
        "run_id",
        "gate_decision",
        "ingestion_result",
        "requested_max_events",
        "schema_version",
    }
)
_GATE_KEYS = frozenset(
    {
        "decision_id",
        "status",
        "allowed",
        "advance_requested",
        "trusted_anchor_id",
        "verification_id",
        "manifest_store_hash",
        "manifest_count",
        "latest_audit_id",
        "schema_version",
    }
)
_INGESTION_KEYS = frozenset(
    {
        "session_id",
        "provider_id",
        "market_id",
        "resumed_from_checkpoint_id",
        "first_accepted_event_id",
        "last_accepted_event_id",
        "accepted_count",
        "final_checkpoint_id",
        "schema_version",
    }
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class JsonRecoveryGatedRunStore:
    """Atomic append-only JSON persistence for recovery-gated run receipts."""

    __slots__ = ("_file_path", "_results")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._results: dict[str, RecoveryGatedIngestionResult] = {}
        self._load_existing()

    def append(self, result: RecoveryGatedIngestionResult) -> str:
        if not isinstance(result, RecoveryGatedIngestionResult):
            raise TypeError(
                "result must be a RecoveryGatedIngestionResult"
            )
        existing = self._results.get(result.run_id)
        if existing is not None:
            if existing != result:
                raise RuntimeError("recovery-gated run identity collision")
            return result.run_id

        candidate = dict(self._results)
        candidate[result.run_id] = result
        self._persist(tuple(candidate.values()))
        self._results = candidate
        return result.run_id

    def get(self, run_id: str) -> RecoveryGatedIngestionResult | None:
        return self._results.get(run_id)

    def iter_results(self) -> Iterator[RecoveryGatedIngestionResult]:
        return iter(tuple(self._results.values()))

    @property
    def result_count(self) -> int:
        return len(self._results)

    @property
    def content_hash(self) -> str:
        return self._compute_content_hash(
            self._serialize_results(tuple(self._results.values()))
        )

    @property
    def file_path(self) -> Path:
        return self._file_path

    def _load_existing(self) -> None:
        temporary_path = self._temporary_path()
        recovering_temporary_file = False
        if self._file_path.is_file():
            source_path = self._file_path
        elif temporary_path.is_file():
            source_path = temporary_path
            recovering_temporary_file = True
        else:
            return

        try:
            loaded = self._load_from_path(source_path)
        except ValueError as exc:
            if recovering_temporary_file:
                raise ValueError(
                    "temporary recovery-gated run recovery failed: "
                    f"{temporary_path}"
                ) from exc
            raise
        if recovering_temporary_file:
            atomic_replace(temporary_path, self._file_path)
        self._results = loaded

    def _load_from_path(
        self,
        path: Path,
    ) -> dict[str, RecoveryGatedIngestionResult]:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"recovery-gated run store is not valid JSON: {path}"
            ) from exc
        if not isinstance(document, dict):
            raise ValueError("recovery-gated run store root must be an object")
        if set(document) != _DOCUMENT_KEYS:
            raise ValueError(
                "recovery-gated run document keys do not match schema"
            )
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported recovery-gated run store schema_version"
            )

        results_data = document["results"]
        if not isinstance(results_data, list):
            raise ValueError("recovery-gated run results must be a list")
        for result_data in results_data:
            self._validate_result_shape(result_data)

        content_hash = document["content_hash"]
        if (
            not isinstance(content_hash, str)
            or _SHA256_PATTERN.fullmatch(content_hash) is None
        ):
            raise ValueError(
                "content_hash must be a lowercase SHA-256 hex digest"
            )
        expected_hash = self._compute_content_hash(results_data)
        if not hmac.compare_digest(content_hash, expected_hash):
            raise ValueError("recovery-gated run store content hash mismatch")

        loaded: dict[str, RecoveryGatedIngestionResult] = {}
        for result_data in results_data:
            result = self._deserialize_result(result_data)
            if result.run_id in loaded:
                raise ValueError(
                    f"duplicate recovery-gated run identity: {result.run_id}"
                )
            loaded[result.run_id] = result
        return loaded

    @classmethod
    def _validate_result_shape(cls, result: Any) -> None:
        if not isinstance(result, dict):
            raise ValueError("each recovery-gated result must be an object")
        if set(result) != _RESULT_KEYS:
            raise ValueError(
                "recovery-gated result keys do not match schema"
            )
        cls._require_keys(
            result["gate_decision"],
            _GATE_KEYS,
            "gate decision",
        )
        cls._require_keys(
            result["ingestion_result"],
            _INGESTION_KEYS,
            "ingestion result",
        )

    @staticmethod
    def _require_keys(
        value: Any,
        expected_keys: frozenset[str],
        field_name: str,
    ) -> None:
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be an object")
        if set(value) != expected_keys:
            raise ValueError(f"{field_name} keys do not match schema")

    @staticmethod
    def _deserialize_result(
        data: dict[str, Any],
    ) -> RecoveryGatedIngestionResult:
        gate_data = data["gate_decision"]
        ingestion_data = data["ingestion_result"]
        try:
            gate_decision = AuditRecoveryGateDecision(
                **{
                    **gate_data,
                    "status": AuditRecoveryGateStatus(gate_data["status"]),
                }
            )
            ingestion_result = CheckpointedIngestionResult(**ingestion_data)
            return RecoveryGatedIngestionResult(
                run_id=data["run_id"],
                gate_decision=gate_decision,
                ingestion_result=ingestion_result,
                requested_max_events=data["requested_max_events"],
                schema_version=data["schema_version"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "invalid recovery-gated ingestion result"
            ) from exc

    def _persist(
        self,
        results: tuple[RecoveryGatedIngestionResult, ...],
    ) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        results_data = self._serialize_results(results)
        document = {
            "schema_version": _SCHEMA_VERSION,
            "content_hash": self._compute_content_hash(results_data),
            "results": results_data,
        }
        temporary_path = self._temporary_path()
        with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary_path, self._file_path)

    @staticmethod
    def _serialize_results(
        results: tuple[RecoveryGatedIngestionResult, ...],
    ) -> list[dict[str, Any]]:
        return [result.canonical_dict() for result in results]

    @staticmethod
    def _compute_content_hash(results_data: list[dict[str, Any]]) -> str:
        material = {
            "schema_version": _SCHEMA_VERSION,
            "results": results_data,
        }
        return hashlib.sha256(
            canonical_json(material).encode("utf-8")
        ).hexdigest()

    def _temporary_path(self) -> Path:
        return self._file_path.with_name(f"{self._file_path.name}.tmp")


__all__ = ["JsonRecoveryGatedRunStore"]
