from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verifier import (
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReceipt,
)
from smart_money.core.serialization import canonical_json
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = (
    "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_store.v1"
)

@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt:
    replay_id: str
    original_verification_id: str
    matches: bool
    schema_version: str = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.original_verification_id, str) or not self.original_verification_id.strip():
            raise ValueError("original_verification_id must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay",
            {"original_verification_id": self.original_verification_id, "schema_version": self.schema_version},
        )
        if self.replay_id != expected:
            raise ValueError("replay_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "original_verification_id": self.original_verification_id,
            "replay_id": self.replay_id,
            "schema_version": self.schema_version,
        }


class JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationStore:
    """Atomic persistence for replay-store verification receipts."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipt: (
            SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReceipt
            | None
        ) = None
        self._load()

    def save(
        self,
        receipt: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReceipt,
    ) -> str:
        if not isinstance(
            receipt,
            SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReceipt,
        ):
            raise TypeError("receipt must be a verification receipt")
        if self._receipt is not None and self._receipt != receipt:
            raise RuntimeError("Solana verification identity collision")
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {"receipt": receipt.canonical_dict(), "schema_version": _SCHEMA_VERSION}
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)
        self._receipt = receipt
        return receipt.verification_id

    def load(self):
        return self._receipt

    def replay(self, expected):
        if self._receipt is None:
            raise ValueError("persisted verification receipt is missing")
        if self._receipt.canonical_dict() != expected.canonical_dict():
            raise ValueError("persisted verification receipt does not match replay")
        schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay.v1"
        return SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt(
            replay_id=deterministic_id(
                "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay",
                {"original_verification_id": expected.verification_id, "schema_version": schema},
            ),
            original_verification_id=expected.verification_id,
            matches=True,
        )

    def _load(self) -> None:
        if not self._file_path.is_file():
            return
        try:
            raw = self._file_path.read_text(encoding="utf-8")
            document: Any = json.loads(raw)
            if document["schema_version"] != _SCHEMA_VERSION:
                raise ValueError("unsupported verification store schema_version")
            data = document["receipt"]
            self._receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReceipt(
                verification_id=data["verification_id"],
                replay_id=data["replay_id"],
                matches=data["matches"],
                schema_version=data["schema_version"],
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid Solana verification store") from exc
        if canonical_json(document) != raw:
            raise ValueError("Solana verification store is not canonical JSON")


class JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore:
    """Atomic persistence for verification-replay receipts."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipt: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt | None = None
        self._load()

    def save(self, receipt):
        if not isinstance(receipt, SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt):
            raise TypeError("receipt must be a verification replay receipt")
        if self._receipt is not None and self._receipt != receipt:
            raise RuntimeError("Solana verification replay identity collision")
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "receipt": receipt.canonical_dict(),
            "schema_version": "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store.v1",
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
            self._receipt = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt(
                replay_id=data["replay_id"],
                original_verification_id=data["original_verification_id"],
                matches=data["matches"],
                schema_version=data["schema_version"],
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid Solana verification replay store") from exc
        if canonical_json(document) != raw:
            raise ValueError("Solana verification replay store is not canonical JSON")

__all__ = [
    "SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayReceipt",
    "JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationStore",
    "JsonSolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReplayStoreVerificationReplayStore",
]
