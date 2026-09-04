from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit import (
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt,
)
from smart_money.core.serialization import canonical_json
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_store.v1"
)


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt:
    replay_id: str
    original_audit_id: str
    matches: bool
    schema_version: str = (
        "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay.v1"
    )

    def __post_init__(self) -> None:
        if not isinstance(self.original_audit_id, str) or not self.original_audit_id.strip():
            raise ValueError("original_audit_id must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != (
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay.v1"
        ):
            raise ValueError("unsupported audit replay schema_version")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay",
            {"original_audit_id": self.original_audit_id, "schema_version": self.schema_version},
        )
        if self.replay_id != expected:
            raise ValueError("replay_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "original_audit_id": self.original_audit_id,
            "replay_id": self.replay_id,
            "schema_version": self.schema_version,
        }


class JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStore:
    """Atomic persistence for the latest audit replay receipt."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipt: (
            SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt
            | None
        ) = None
        self._load()

    def save(
        self,
        receipt: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt,
    ) -> str:
        if not isinstance(
            receipt,
            SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt,
        ):
            raise TypeError("receipt must be an audit replay receipt")
        if self._receipt is not None and self._receipt != receipt:
            raise RuntimeError("Solana audit replay identity collision")
        self._persist(receipt)
        self._receipt = receipt
        return receipt.replay_id

    def load(
        self,
    ) -> (
        SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt
        | None
    ):
        return self._receipt

    def _load(self) -> None:
        if not self._file_path.is_file():
            return
        try:
            raw = self._file_path.read_text(encoding="utf-8")
            document: Any = json.loads(raw)
            if document["schema_version"] != (
                "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store.v1"
            ):
                raise ValueError("unsupported audit replay store schema_version")
            data = document["receipt"]
            receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt(
                replay_id=data["replay_id"],
                original_audit_id=data["original_audit_id"],
                matches=data["matches"],
                schema_version=data["schema_version"],
            )
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError("invalid Solana audit replay store") from exc
        if canonical_json(document) != raw:
            raise ValueError("Solana audit replay store is not canonical JSON")
        self._receipt = receipt

    def _persist(
        self,
        receipt: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt,
    ) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "receipt": receipt.canonical_dict(),
            "schema_version": (
                "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store.v1"
            ),
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


class JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditStore:
    """Atomic persistence for the latest replay-store audit receipt."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipt: (
            SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt | None
        ) = None
        self._load()

    def save(
        self,
        receipt: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt,
    ) -> str:
        if not isinstance(
            receipt,
            SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt,
        ):
            raise TypeError("receipt must be a replay-store audit receipt")
        if self._receipt is not None and self._receipt != receipt:
            raise RuntimeError("Solana replay-store audit identity collision")
        self._persist(receipt)
        self._receipt = receipt
        return receipt.audit_id

    def load(
        self,
    ) -> SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt | None:
        return self._receipt

    @property
    def audit_id(self) -> str | None:
        return None if self._receipt is None else self._receipt.audit_id

    def replay(
        self,
        expected: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt,
    ) -> SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt:
        if self._receipt is None:
            raise ValueError("persisted Solana audit receipt is missing")
        if not isinstance(
            expected,
            SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt,
        ):
            raise TypeError("expected must be a replay-store audit receipt")
        if self._receipt.canonical_dict() != expected.canonical_dict():
            raise ValueError("persisted Solana audit receipt does not match replay")
        return SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt(
            replay_id=deterministic_id(
                "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay",
                {
                    "original_audit_id": expected.audit_id,
                    "schema_version": (
                        "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay.v1"
                    ),
                },
            ),
            original_audit_id=expected.audit_id,
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
            if not isinstance(document, dict) or set(document) != {
                "receipt",
                "schema_version",
            }:
                raise ValueError("store keys do not match schema")
            if document["schema_version"] != _SCHEMA_VERSION:
                raise ValueError("unsupported audit store schema_version")
            data = document["receipt"]
            if not isinstance(data, dict):
                raise ValueError("invalid replay-store audit receipt")
            receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt(
                expected_replay_id=data["expected_replay_id"],
                persisted_replay_id=data["persisted_replay_id"],
                matches=data["matches"],
                file_exists=data["file_exists"],
                mismatches=tuple(data["mismatches"]),
                schema_version=data["schema_version"],
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid Solana replay-store audit store") from exc
        if canonical_json(document) != raw:
            raise ValueError("Solana replay-store audit store is not canonical JSON")
        if recovering:
            atomic_replace(temporary, self._file_path)
        self._receipt = receipt

    def _persist(
        self,
        receipt: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReceipt,
    ) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "receipt": receipt.canonical_dict(),
            "schema_version": _SCHEMA_VERSION,
        }
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)


__all__ = [
    "JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStore",
    "JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditStore",
    "SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayReceipt",
]
