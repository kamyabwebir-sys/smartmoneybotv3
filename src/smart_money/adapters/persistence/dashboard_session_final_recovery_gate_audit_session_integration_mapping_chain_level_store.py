from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_binding_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingReceipt,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelAuditReceipt,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_persistence_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = (
    "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_store.v1"
)
_Receipt = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelAuditReceipt


class JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore:
    """Atomic persistence for M71.3 chain-level audit receipts."""

    __slots__ = ("_file_path", "_receipts")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipts: dict[
            str,
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelAuditReceipt,
        ] = {}
        self._load()

    def append(
        self,
        receipt: _Receipt,
    ) -> str:
        if not isinstance(receipt, _Receipt):
            raise TypeError(
                "receipt must be a "
                "DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelAuditReceipt"
            )
        receipt_id = receipt.audit_id
        existing = self._receipts.get(receipt_id)
        if existing is not None:
            if existing != receipt:
                raise RuntimeError("chain-level audit receipt identity collision")
            return receipt_id
        candidate = dict(self._receipts)
        candidate[receipt_id] = receipt
        self._persist(tuple(candidate.values()))
        self._receipts = candidate
        return receipt_id

    def get(
        self,
        audit_id: str,
    ) -> _Receipt | None:
        return self._receipts.get(audit_id)

    def iter_receipts(
        self,
    ) -> Iterator[_Receipt]:
        return iter(tuple(self._receipts.values()))

    @property
    def receipt_count(self) -> int:
        return len(self._receipts)

    @property
    def content_hash(self) -> str:
        return _digest([_record(item) for item in self._receipts.values()])

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
            raise ValueError("chain-level audit receipt store is not valid JSON") from exc

        if not isinstance(document, dict) or set(document) != {
            "content_hash",
            "receipts",
            "schema_version",
        }:
            raise ValueError("chain-level audit receipt store keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError("unsupported chain-level audit receipt store schema_version")
        records = document["receipts"]
        if not isinstance(records, list) or _digest(records) != document["content_hash"]:
            raise ValueError("chain-level audit receipt store content hash mismatch")
        if canonical_json(document) != raw:
            raise ValueError("chain-level audit receipt store is not canonical JSON")

        loaded: dict[
            str,
            _Receipt,
        ] = {}
        for record in records:
            try:
                receipt = _from_record(record)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("invalid chain-level audit receipt") from exc
            receipt_id = receipt.audit_id
            if receipt_id in loaded:
                raise ValueError("duplicate chain-level audit receipt ID")
            loaded[receipt_id] = receipt

        if recovering:
            atomic_replace(temporary, self._file_path)
        self._receipts = loaded

    def _persist(
        self,
        receipts: tuple[
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelAuditReceipt,
            ...,
        ],
    ) -> None:
        if self._file_path.parent != Path("."):
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
        records = [_record(item) for item in receipts]
        document = {
            "content_hash": _digest(records),
            "receipts": records,
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


def _record(
    receipt: _Receipt,
) -> dict[str, object]:
    return {
        "chain_entry_count": receipt.chain_entry_count,
        "chain_hash": receipt.chain_hash,
        "chain_id": receipt.chain_id,
        "chain_entry_mapping_presence": receipt.chain_entry_mapping_presence,
        "chain_entry_mapping_replay_presence": receipt.chain_entry_mapping_replay_presence,
        "mapping_chain_binding": receipt.mapping_chain_binding.canonical_dict(),
        "mapping_chain_persistence": receipt.mapping_chain_persistence.canonical_dict(),
        "mapping_id": receipt.mapping_id,
        "mapping_replay_persistence": receipt.mapping_replay_persistence.canonical_dict(),
        "mapping_replay_verification_id": receipt.mapping_replay_verification_id,
        "mismatches": list(receipt.mismatches),
        "matches": receipt.matches,
        "decision": receipt.decision,
        "schema_version": receipt.schema_version,
    }


def _from_record(
    record: dict[str, object],
) -> _Receipt:
    binding = dict(record["mapping_chain_binding"])
    binding["mismatches"] = tuple(binding["mismatches"])
    persistence = dict(record["mapping_chain_persistence"])
    persistence["mismatches"] = tuple(persistence["mismatches"])
    replay_persistence = dict(record["mapping_replay_persistence"])
    replay_persistence["mismatches"] = tuple(replay_persistence["mismatches"])
    return _Receipt(
        chain_entry_count=record["chain_entry_count"],
        chain_hash=record["chain_hash"],
        chain_id=record["chain_id"],
        chain_entry_mapping_presence=record["chain_entry_mapping_presence"],
        chain_entry_mapping_replay_presence=record["chain_entry_mapping_replay_presence"],
        mapping_chain_binding=(
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingReceipt(
                **binding
            )
        ),
        mapping_chain_persistence=(
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt(
                **persistence
            )
        ),
        mapping_id=record["mapping_id"],
        mapping_replay_persistence=(
            DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt(
                **replay_persistence
            )
        ),
        mapping_replay_verification_id=record["mapping_replay_verification_id"],
        mismatches=tuple(record["mismatches"]),
        matches=record["matches"],
        decision=record["decision"],
        schema_version=record["schema_version"],
    )


__all__ = [
    "JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore",
]
