from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding_replay_store_verification_replay_store_audit import (
    SolanaVerificationReplayStorePersistenceAuditReplayReceipt,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "solana_verification_replay_store_persistence_audit_replay_store.v1"


class JsonSolanaVerificationReplayStorePersistenceAuditReplayStore:
    """Atomic persistence for verification replay-store audit replay receipts."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipt: SolanaVerificationReplayStorePersistenceAuditReplayReceipt | None = None
        self._load()

    def save(self, receipt: SolanaVerificationReplayStorePersistenceAuditReplayReceipt) -> str:
        if not isinstance(receipt, SolanaVerificationReplayStorePersistenceAuditReplayReceipt):
            raise TypeError("receipt must be a verification replay audit replay receipt")
        if self._receipt is not None and self._receipt != receipt:
            raise RuntimeError("Solana audit replay identity collision")
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {"receipt": receipt.canonical_dict(), "schema_version": _SCHEMA_VERSION}
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
            if document["schema_version"] != _SCHEMA_VERSION:
                raise ValueError("unsupported audit replay store schema_version")
            data = document["receipt"]
            self._receipt = SolanaVerificationReplayStorePersistenceAuditReplayReceipt(
                replay_id=data["replay_id"],
                original_audit_id=data["original_audit_id"],
                matches=data["matches"],
                schema_version=data["schema_version"],
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid Solana audit replay persistence store") from exc
        if canonical_json(document) != raw:
            raise ValueError("Solana audit replay persistence store is not canonical JSON")


__all__ = ["JsonSolanaVerificationReplayStorePersistenceAuditReplayStore"]
