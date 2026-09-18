from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from smart_money.core.serialization import canonicalize
from smart_money.domain.market_state import MarketStateChange
from smart_money.domain.truth import TruthClassification
from smart_money.ingestion.contracts import EvidencePayload

_TRUTH_CLASSIFICATION = TruthClassification.canonical_observation()


def _mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{field_name} keys must be strings")
    return value


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


@dataclass(frozen=True, slots=True)
class CanonicalMarketStateObservation:
    """Typed parser and projector for canonical market-state evidence."""

    EVIDENCE_TYPE: ClassVar[str] = "canonical_market_state_observation"
    AUTHORITY: ClassVar[str] = _TRUTH_CLASSIFICATION.authority.value
    CLASSIFICATION: ClassVar[str] = _TRUTH_CLASSIFICATION.layer.value
    VERIFICATION_STATUS: ClassVar[str] = (
        _TRUTH_CLASSIFICATION.verification_status.value
    )

    payload: EvidencePayload
    event_id: str
    source_event_id: str
    chain_id: str
    market_id: str
    source_schema_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        if self.payload.evidence_type != self.EVIDENCE_TYPE:
            raise ValueError("unsupported canonical observation evidence_type")
        state_change = _mapping(
            self.payload.data.get("market_state_change"),
            "market_state_change",
        )
        provenance = _mapping(
            self.payload.metadata.get("provenance"),
            "provenance",
        )
        if set(self.payload.data) != {"market_state_change"}:
            raise ValueError("canonical observation data keys do not match")
        if set(self.payload.metadata) != {
            "authority",
            "classification",
            "provenance",
            "verification_status",
        }:
            raise ValueError("canonical observation metadata keys do not match")
        expected_metadata = _TRUTH_CLASSIFICATION.metadata_fields()
        for key, expected in expected_metadata.items():
            if self.payload.metadata.get(key) != expected:
                raise ValueError(f"canonical observation {key} mismatch")
        expected_provenance = {
            "chain_id": self.chain_id,
            "market_id": self.market_id,
            "source_event_id": self.source_event_id,
            "source_id": self.payload.source_id,
            "source_schema_version": self.source_schema_version,
        }
        if canonicalize(provenance) != canonicalize(expected_provenance):
            raise ValueError("canonical observation provenance mismatch")
        expected_change_fields = {
            "event_id": self.event_id,
            "source_event_id": self.source_event_id,
            "source_id": self.payload.source_id,
            "schema_version": self.source_schema_version,
        }
        for key, expected in expected_change_fields.items():
            if state_change.get(key) != expected:
                raise ValueError(f"market_state_change {key} mismatch")

    @classmethod
    def from_change(
        cls,
        change: MarketStateChange,
    ) -> CanonicalMarketStateObservation:
        if not isinstance(change, MarketStateChange):
            raise TypeError("change must be a MarketStateChange")
        payload = EvidencePayload(
            source_id=change.source_id,
            evidence_type=cls.EVIDENCE_TYPE,
            timestamp=change.occurred_at,
            data={"market_state_change": change.canonical_dict()},
            metadata={
                **_TRUTH_CLASSIFICATION.metadata_fields(),
                "provenance": {
                    "chain_id": change.chain.canonical_id,
                    "market_id": change.market.canonical_id,
                    "source_event_id": change.source_event_id,
                    "source_id": change.source_id,
                    "source_schema_version": change.schema_version,
                },
            },
        )
        return cls(
            payload=payload,
            event_id=change.event_id,
            source_event_id=change.source_event_id,
            chain_id=change.chain.canonical_id,
            market_id=change.market.canonical_id,
            source_schema_version=change.schema_version,
        )

    @classmethod
    def from_payload(
        cls,
        payload: EvidencePayload,
    ) -> CanonicalMarketStateObservation:
        if not isinstance(payload, EvidencePayload):
            raise TypeError("payload must be an EvidencePayload")
        state_change = _mapping(
            payload.data.get("market_state_change"),
            "market_state_change",
        )
        provenance = _mapping(
            payload.metadata.get("provenance"),
            "provenance",
        )
        return cls(
            payload=payload,
            event_id=_text(state_change.get("event_id"), "event_id"),
            source_event_id=_text(
                provenance.get("source_event_id"),
                "source_event_id",
            ),
            chain_id=_text(provenance.get("chain_id"), "chain_id"),
            market_id=_text(provenance.get("market_id"), "market_id"),
            source_schema_version=_text(
                provenance.get("source_schema_version"),
                "source_schema_version",
            ),
        )

    @classmethod
    def receipt_mismatches(
        cls,
        payload: EvidencePayload,
        *,
        provider_id: str,
        event_id: str,
        source_event_id: str,
        market_id: str,
    ) -> tuple[str, ...]:
        """Return stable receipt-binding mismatch codes for one payload."""
        mismatches: list[str] = []
        if payload.evidence_type != cls.EVIDENCE_TYPE:
            mismatches.append("evidence_type")
        state_change = payload.data.get("market_state_change")
        if not isinstance(state_change, Mapping):
            mismatches.append("evidence_payload")
        else:
            if state_change.get("event_id") != event_id:
                mismatches.append("evidence_event_id")
            if state_change.get("source_event_id") != source_event_id:
                mismatches.append("evidence_source_event_id")
        provenance = payload.metadata.get("provenance")
        if payload.source_id != provider_id:
            mismatches.append("evidence_provider_id")
        if not isinstance(provenance, Mapping):
            mismatches.append("evidence_payload")
        else:
            if provenance.get("source_id") != provider_id:
                mismatches.append("evidence_provider_id")
            if provenance.get("source_event_id") != source_event_id:
                mismatches.append("evidence_source_event_id")
            if provenance.get("market_id") != market_id:
                mismatches.append("evidence_market_id")
        try:
            cls.from_payload(payload)
        except (TypeError, ValueError):
            if not mismatches:
                mismatches.append("evidence_payload")
        return tuple(dict.fromkeys(mismatches))

    @staticmethod
    def ordering_key(
        payload: EvidencePayload,
    ) -> tuple[int, int] | None:
        """Read the canonical ordering key without interpreting the event."""
        state_change = payload.data.get("market_state_change")
        if not isinstance(state_change, Mapping):
            return None
        chain_sequence = state_change.get("chain_sequence")
        event_index = state_change.get("event_index")
        if (
            isinstance(chain_sequence, bool)
            or not isinstance(chain_sequence, int)
            or isinstance(event_index, bool)
            or not isinstance(event_index, int)
        ):
            return None
        return chain_sequence, event_index


__all__ = ["CanonicalMarketStateObservation"]
