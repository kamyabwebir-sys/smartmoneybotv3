from __future__ import annotations

from typing import Any

from contracts import EvidencePayload, IngestionResult
from smart_money.ingestion.errors import InvalidPayloadError


class EvidenceIngestionProvider:
    """Compatibility facade for the ledger-backed evidence ingestion flow."""

    def __init__(self, registry: Any = None, ledger: Any = None) -> None:
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

        ledger_contains = getattr(self._ledger, "contains", None)
        already_grounded = bool(
            callable(ledger_contains) and ledger_contains(canonical_id)
        )
        if canonical_id in self._seen_ids or already_grounded:
            self._seen_ids.add(canonical_id)
            return IngestionResult(
                accepted=False,
                canonical_id=canonical_id,
                message="Duplicate ignored.",
            )

        if self._ledger is not None:
            recorded_id = self._ledger.record(payload)
            if recorded_id != canonical_id:
                raise InvalidPayloadError(
                    "ledger returned an identity inconsistent with the payload"
                )

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
        return isinstance(legacy_registry, dict) and evidence_type in legacy_registry
