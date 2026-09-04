import hashlib
import json
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .contracts import IngestionCandle, MarketSnapshot
from .contracts import EvidencePayload as CanonicalEvidencePayload
from .contracts import IngestionResult as CanonicalIngestionResult


class BaseDataProvider(ABC):
    @abstractmethod
    async def get_candles(
        self, symbol: str, interval: str, limit: int
    ) -> Sequence[IngestionCandle]:
        raise NotImplementedError

    @abstractmethod
    async def stream_candles(
        self, symbol: str, interval: str
    ) -> AsyncIterable[IngestionCandle]:
        raise NotImplementedError

    @abstractmethod
    async def get_snapshot(self, symbol: str) -> MarketSnapshot:
        raise NotImplementedError


def get_canonical_id(payload_data: Dict[str, Any]) -> str:
    """Generates a deterministic SHA256 canonical ID from payload dictionary."""
    serialized = json.dumps(payload_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvidencePayload:
    source: str
    data: Dict[str, Any]
    observed_slot: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source or not isinstance(self.source, str):
            raise ValueError("source must be a non-empty string")
        if not isinstance(self.data, dict) or not self.data:
            raise ValueError("data must be a non-empty dictionary")
        if not isinstance(self.observed_slot, int) or self.observed_slot < 0:
            raise ValueError("observed_slot must be a non-negative integer")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")


@dataclass(frozen=True)
class IngestionResult:
    canonical_id: str
    status: str
    is_duplicate: bool
    evidence_payload: EvidencePayload
    error_message: Optional[str] = None


class EvidenceGroundingLedger:
    """In-memory append-only ledger for ingested evidence."""

    def __init__(self) -> None:
        self._records: Dict[str, Tuple[EvidencePayload, IngestionResult]] = {}
        self._sequence: List[str] = []

    def has(self, canonical_id: str) -> bool:
        return canonical_id in self._records

    def append(self, canonical_id: str, payload: EvidencePayload, result: IngestionResult) -> None:
        if canonical_id in self._records:
            return
        self._records[canonical_id] = (payload, result)
        self._sequence.append(canonical_id)

    def get(self, canonical_id: str) -> Optional[Tuple[EvidencePayload, IngestionResult]]:
        return self._records.get(canonical_id)

    def count(self) -> int:
        return len(self._sequence)

    def get_sequence(self) -> List[str]:
        return list(self._sequence)


class EvidenceIngestionProvider:
    """Deterministic, fail-closed, in-memory evidence ingestion provider."""

    def __init__(
        self,
        registry: Any = None,
        ledger: Any = None,
    ) -> None:
        self._registry = registry
        self._external_ledger = ledger
        self._seen_ids: set[str] = set()
        self.ledger = ledger if ledger is not None else EvidenceGroundingLedger()

    def ingest(
        self, payload: EvidencePayload | CanonicalEvidencePayload
    ) -> IngestionResult | CanonicalIngestionResult:
        if isinstance(payload, CanonicalEvidencePayload):
            return self._ingest_canonical(payload)
        if not isinstance(payload, EvidencePayload):
            raise TypeError("payload must be an evidence payload")

        payload.validate()

        canonical_id = get_canonical_id(payload.data)

        if self.ledger.has(canonical_id):
            return IngestionResult(
                canonical_id=canonical_id,
                status="IDEMPOTENT_DUPLICATE",
                is_duplicate=True,
                evidence_payload=payload,
                error_message=None,
            )

        result = IngestionResult(
            canonical_id=canonical_id,
            status="ACCEPTED",
            is_duplicate=False,
            evidence_payload=payload,
            error_message=None,
        )
        self.ledger.append(canonical_id, payload, result)
        return result

    def _ingest_canonical(
        self, payload: CanonicalEvidencePayload
    ) -> CanonicalIngestionResult:
        canonical_id = payload.get_canonical_id()
        if self._registry is not None and not self._is_type_supported(
            payload.evidence_type
        ):
            return CanonicalIngestionResult(
                accepted=False,
                canonical_id=canonical_id,
                message=f"Unsupported evidence type: {payload.evidence_type}",
            )

        contains = getattr(self._external_ledger, "contains", None)
        duplicate = canonical_id in self._seen_ids or (
            callable(contains) and contains(canonical_id)
        )
        if duplicate:
            self._seen_ids.add(canonical_id)
            return CanonicalIngestionResult(
                accepted=False,
                canonical_id=canonical_id,
                message="Duplicate ignored.",
            )

        if self._external_ledger is not None:
            append = getattr(self._external_ledger, "append", None)
            if not callable(append):
                raise TypeError("ledger must provide append")
            recorded_id = append(payload)
            if recorded_id != canonical_id:
                raise RuntimeError("ledger returned a mismatched canonical identity")

        self._seen_ids.add(canonical_id)
        return CanonicalIngestionResult(accepted=True, canonical_id=canonical_id)

    def _is_type_supported(self, evidence_type: str) -> bool:
        list_ids = getattr(self._registry, "list_ids", None)
        if callable(list_ids):
            try:
                return evidence_type in tuple(list_ids())
            except (TypeError, ValueError, KeyError):
                return False
        legacy_registry = getattr(self._registry, "_registry", None)
        return isinstance(legacy_registry, dict) and evidence_type in legacy_registry
