from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding import (
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt,
)
from smart_money.core.serialization import canonical_json
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_store.v1"
)

@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayReceipt:
    replay_id: str
    original_binding_id: str
    matches: bool
    schema_version: str = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.original_binding_id, str) or not self.original_binding_id.strip():
            raise ValueError("original_binding_id must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay",
            {"original_binding_id": self.original_binding_id, "schema_version": self.schema_version},
        )
        if self.replay_id != expected:
            raise ValueError("replay_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "original_binding_id": self.original_binding_id,
            "replay_id": self.replay_id,
            "schema_version": self.schema_version,
        }


class JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingStore:
    """Atomic persistence for the latest audit-chain binding receipt."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipt: (
            SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt
            | None
        ) = None
        self._load()

    def save(
        self,
        receipt: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt,
    ) -> str:
        if not isinstance(
            receipt,
            SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt,
        ):
            raise TypeError("receipt must be an audit-chain binding receipt")
        if self._receipt is not None and self._receipt != receipt:
            raise RuntimeError("Solana audit-chain binding identity collision")
        self._persist(receipt)
        self._receipt = receipt
        return receipt.binding_id

    def load(
        self,
    ) -> SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt | None:
        return self._receipt

    @property
    def binding_id(self) -> str | None:
        return None if self._receipt is None else self._receipt.binding_id

    def replay(self, expected):
        if self._receipt is None:
            raise ValueError("persisted audit-chain binding is missing")
        if self._receipt.canonical_dict() != expected.canonical_dict():
            raise ValueError("persisted audit-chain binding does not match replay")
        schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay.v1"
        return SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayReceipt(
            replay_id=deterministic_id(
                "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay",
                {"original_binding_id": expected.binding_id, "schema_version": schema},
            ),
            original_binding_id=expected.binding_id,
            matches=True,
        )

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
            document: Any = json.loads(raw)
            if not isinstance(document, dict) or set(document) != {"receipt", "schema_version"}:
                raise ValueError("store keys do not match schema")
            if document["schema_version"] != _SCHEMA_VERSION:
                raise ValueError("unsupported audit-chain binding store schema_version")
            data = document["receipt"]
            if not isinstance(data, dict):
                raise ValueError("invalid audit-chain binding receipt")
            receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt(
                binding_id=data["binding_id"],
                verification_id=data["verification_id"],
                prior_audit_id=data["prior_audit_id"],
                matches=data["matches"],
                schema_version=data["schema_version"],
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid Solana audit-chain binding store") from exc
        if canonical_json(document) != raw:
            raise ValueError("Solana audit-chain binding store is not canonical JSON")
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._receipt = receipt

    def _persist(
        self,
        receipt: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt,
    ) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {"receipt": receipt.canonical_dict(), "schema_version": _SCHEMA_VERSION}
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


class JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStore:
    """Atomic persistence for the audit-chain binding replay receipt."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipt: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayReceipt | None = None
        self._load()

    def save(self, receipt: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayReceipt) -> str:
        if not isinstance(receipt, SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayReceipt):
            raise TypeError("receipt must be an audit-chain binding replay receipt")
        if self._receipt is not None and self._receipt != receipt:
            raise RuntimeError("Solana audit-chain binding replay identity collision")
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "receipt": receipt.canonical_dict(),
            "schema_version": "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store.v1",
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)
        self._receipt = receipt
        return receipt.replay_id

    def load(self):
        return self._receipt

    def _load(self) -> None:
        if not self._file_path.is_file():
            return
        try:
            raw = self._file_path.read_text(encoding="utf-8")
            document: Any = json.loads(raw)
            data = document["receipt"]
            self._receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayReceipt(
                replay_id=data["replay_id"],
                original_binding_id=data["original_binding_id"],
                matches=data["matches"],
                schema_version=data["schema_version"],
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid Solana audit-chain binding replay store") from exc
        if canonical_json(document) != raw:
            raise ValueError("Solana audit-chain binding replay store is not canonical JSON")


__all__ = [
    "SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayReceipt",
    "JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingStore",
    "JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStore",
]
