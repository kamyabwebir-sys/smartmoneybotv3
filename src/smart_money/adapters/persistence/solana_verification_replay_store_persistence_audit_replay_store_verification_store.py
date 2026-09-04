from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.solana_verification_replay_store_persistence_audit_replay_store_verifier import (
    SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt,
)
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = (
    "solana_verification_replay_store_persistence_audit_replay_store_verification_store.v1"
)


class JsonSolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationStore:
    """Durable canonical store for chain-level verification receipts."""

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._receipt: (
            SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt | None
        ) = None
        self._load()

    def save(
        self,
        receipt: SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt,
    ) -> str:
        if not isinstance(
            receipt,
            SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt,
        ):
            raise TypeError("receipt must be a verification receipt")
        if self._receipt is not None and self._receipt != receipt:
            raise RuntimeError("Solana verification receipt identity collision")
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

    def load(
        self,
    ) -> SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt | None:
        return self._receipt

    def _load(self) -> None:
        if not self._file_path.is_file():
            return
        try:
            raw = self._file_path.read_text(encoding="utf-8")
            document: Any = json.loads(raw)
            if document["schema_version"] != _SCHEMA_VERSION:
                raise ValueError("unsupported verification store schema_version")
            data = document["receipt"]
            self._receipt = (
                SolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationReceipt(
                    verification_id=data["verification_id"],
                    replay_id=data["replay_id"],
                    matches=data["matches"],
                    schema_version=data["schema_version"],
                )
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid Solana verification receipt store") from exc
        if canonical_json(document) != raw:
            raise ValueError("Solana verification receipt store is not canonical JSON")


__all__ = [
    "JsonSolanaVerificationReplayStorePersistenceAuditReplayStoreVerificationStore",
]
