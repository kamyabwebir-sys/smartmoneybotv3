from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, Sequence
from typing import Any

from .contracts import EvidencePayload, IngestionCandle, IngestionResult, MarketSnapshot
from .errors import InvalidPayloadError
from .ledger import EvidenceLedger


class BaseDataProvider(ABC):
    """I/O adapter contract consumed by the ingestion pipeline."""

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int,
    ) -> Sequence[IngestionCandle]:
        raise NotImplementedError

    @abstractmethod
    async def stream_candles(
        self,
        symbol: str,
        interval: str,
    ) -> AsyncIterable[IngestionCandle]:
        raise NotImplementedError

    @abstractmethod
    async def get_snapshot(self, symbol: str) -> MarketSnapshot:
        raise NotImplementedError


class EvidenceIngestionProvider:
    """Validate and ground immutable evidence without external side effects."""

    def __init__(
        self,
        registry: Any = None,
        ledger: EvidenceLedger | None = None,
    ) -> None:
        self._seen_ids: set[str] = set()
        self._registry = registry
        self._ledger = ledger

    def ingest(self, payload: EvidencePayload) -> IngestionResult:
        if not isinstance(payload, EvidencePayload):
            raise InvalidPayloadError("payload must be an EvidencePayload")
        if not payload.source_id or not payload.evidence_type or payload.timestamp <= 0:
            raise InvalidPayloadError(
                "Missing source_id, evidence_type, or invalid timestamp."
            )

        canonical_id = payload.get_canonical_id()

        if self._registry is not None and not self._is_type_supported(
            payload.evidence_type
        ):
            return IngestionResult(
                accepted=False,
                canonical_id=canonical_id,
                message=f"Unsupported evidence type: {payload.evidence_type}",
            )

        if canonical_id in self._seen_ids or (
            self._ledger is not None and self._ledger.contains(canonical_id)
        ):
            self._seen_ids.add(canonical_id)
            return IngestionResult(
                accepted=False,
                canonical_id=canonical_id,
                message="Duplicate ignored.",
            )

        if self._ledger is not None:
            recorded_id = self._ledger.append(payload)
            if recorded_id != canonical_id:
                raise RuntimeError("ledger returned a mismatched canonical identity")

        self._seen_ids.add(canonical_id)
        return IngestionResult(accepted=True, canonical_id=canonical_id)

    def _is_type_supported(self, evidence_type: str) -> bool:
        list_ids = getattr(self._registry, "list_ids", None)
        if callable(list_ids):
            try:
                return evidence_type in tuple(list_ids())
            except (TypeError, ValueError, KeyError):
                return False

        legacy_registry = getattr(self._registry, "_registry", None)
        if isinstance(legacy_registry, dict):
            return evidence_type in legacy_registry

        return False
