from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapper as mapping_model,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = (
    "dashboard_session_final_recovery_gate_audit_session_integration_mapping_store.v1"
)


class JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore:
    """Atomic persistence for final recovery gate session integration mappings."""

    __slots__ = ("_file_path", "_mappings")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._mappings: dict[
            str,
            mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
        ] = {}
        self._load()

    def append(
        self,
        mapping: mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
    ) -> str:
        if not isinstance(
            mapping,
            mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
        ):
            raise TypeError(
                "mapping must be a "
                "DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt"
            )
        existing = self._mappings.get(mapping.mapping_id)
        if existing is not None:
            if existing != mapping:
                raise RuntimeError(
                    "integration mapping identity collision"
                )
            return mapping.mapping_id

        candidate = dict(self._mappings)
        candidate[mapping.mapping_id] = mapping
        self._persist(tuple(candidate.values()))
        self._mappings = candidate
        return mapping.mapping_id

    def get(
        self,
        mapping_id: str,
    ) -> mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt | None:
        return self._mappings.get(mapping_id)

    def iter_mappings(
        self,
    ) -> Iterator[
        mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt
    ]:
        return iter(tuple(self._mappings.values()))

    @property
    def mapping_count(self) -> int:
        return len(self._mappings)

    @property
    def content_hash(self) -> str:
        return _digest([item.canonical_dict() for item in self._mappings.values()])

    def _load(self) -> None:
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        if self._file_path.is_file():
            source, recovering = self._file_path, False
        elif temporary.is_file():
            source, recovering = temporary, True
        else:
            return

        try:
            raw = source.read_text(encoding="utf-8")
            document = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                "session final recovery gate integration mapping store is not valid JSON"
            ) from exc

        if not isinstance(document, dict) or set(document) != {
            "content_hash",
            "mappings",
            "schema_version",
        }:
            raise ValueError(
                "session final recovery gate integration mapping store keys do not match schema"
            )
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported session final recovery gate integration mapping store schema_version"
            )
        records = document["mappings"]
        if not isinstance(records, list) or _digest(records) != document["content_hash"]:
            raise ValueError(
                "session final recovery gate integration mapping store content hash mismatch"
            )
        if canonical_json(document) != raw:
            raise ValueError(
                "session final recovery gate integration mapping store is not canonical JSON"
            )

        loaded: dict[
            str,
            mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
        ] = {}
        for record in records:
            try:
                mapping = (
                    mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt(
                    chain_id=record["chain_id"],
                    chain_hash=record["chain_hash"],
                    chain_entry_count=record["chain_entry_count"],
                    chain_replay_verification_id=record[
                        "chain_replay_verification_id"
                    ],
                    full_audit_receipt_id=record["full_audit_receipt_id"],
                    full_audit_verification_id=record[
                        "full_audit_verification_id"
                    ],
                    binding_receipt_id=record["binding_receipt_id"],
                    integration_session_id=record["integration_session_id"],
                    previous_integration_session_id=record[
                        "previous_integration_session_id"
                    ],
                    decision=record["decision"],
                    reason_code=record["reason_code"],
                    schema_version=record["schema_version"],
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    "invalid session final recovery gate integration mapping"
                ) from exc
            if mapping.mapping_id in loaded:
                raise ValueError(
                    "duplicate session final recovery gate integration mapping ID"
                )
            loaded[mapping.mapping_id] = mapping

        if recovering:
            atomic_replace(temporary, self._file_path)
        self._mappings = loaded

    def _persist(
        self,
        mappings: tuple[
            mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
            ...,
        ],
    ) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

        records = [item.canonical_dict() for item in mappings]
        document = {
            "content_hash": _digest(records),
            "mappings": records,
            "schema_version": _SCHEMA_VERSION,
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


__all__ = [
    "JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore",
]
