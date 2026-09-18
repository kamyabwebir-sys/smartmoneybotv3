from __future__ import annotations

import hmac
import os
import re
from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.json_ledger import (
    EvidenceGroundingLedger,
)
from smart_money.core.serialization import canonicalize
from smart_money.ingestion.contracts import EvidencePayload


class DurableJsonEvidenceLedger:
    """Single-writer, copy-on-write JSON ledger with durable append semantics."""

    __slots__ = ("_file_path", "_ledger")

    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._ledger = EvidenceGroundingLedger()
        self._ledger.load_from_disk(self._file_path)

    def append(self, payload: EvidencePayload) -> str:
        if not isinstance(payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")

        canonical_id = payload.get_canonical_id()
        existing = self._ledger.get(canonical_id)
        if existing is not None:
            if canonicalize(existing.canonical_dict()) != canonicalize(
                payload.canonical_dict()
            ):
                raise RuntimeError("canonical evidence identity collision")
            return canonical_id

        candidate = EvidenceGroundingLedger()
        for retained_payload in self._ledger.iter_payloads():
            candidate.append(retained_payload)
        recorded_id = candidate.append(payload)
        if recorded_id != canonical_id:
            raise RuntimeError("candidate ledger returned a mismatched identity")
        candidate.save_to_disk(self._file_path)
        self._ledger = candidate
        return canonical_id

    def contains(self, canonical_id: str) -> bool:
        return self._ledger.contains(canonical_id)

    def get(self, canonical_id: str) -> EvidencePayload | None:
        return self._ledger.get(canonical_id)

    def iter_payloads(self) -> Iterator[EvidencePayload]:
        return self._ledger.iter_payloads()

    @property
    def entry_count(self) -> int:
        return self._ledger.entry_count

    @property
    def file_path(self) -> Path:
        return self._file_path

    @property
    def content_hash(self) -> str:
        return self._ledger.content_hash

    def contains_content_hash(self, content_hash: str) -> bool:
        """Return whether a hash identifies any canonical append-only prefix."""
        if not isinstance(content_hash, str):
            raise TypeError("content_hash must be a string")
        digest = content_hash.strip()
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError(
                "content_hash must be a lowercase SHA-256 hex digest"
            )

        prefix = EvidenceGroundingLedger()
        if hmac.compare_digest(prefix.content_hash, digest):
            return True
        for payload in self._ledger.iter_payloads():
            prefix.append(payload)
            if hmac.compare_digest(prefix.content_hash, digest):
                return True
        return False


__all__ = ["DurableJsonEvidenceLedger"]
