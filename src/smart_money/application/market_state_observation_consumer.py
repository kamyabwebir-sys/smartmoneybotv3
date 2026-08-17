from __future__ import annotations

from dataclasses import dataclass

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.serialization import canonicalize
from smart_money.domain.market_state import MarketStateChange
from smart_money.ingestion.contracts import EvidencePayload

_EVIDENCE_TYPE = "canonical_market_state_observation"


def make_canonical_market_state_observation(
    change: MarketStateChange,
) -> EvidencePayload:
    """Project one canonical state change into immutable observation evidence."""
    if not isinstance(change, MarketStateChange):
        raise TypeError("change must be a MarketStateChange")
    return EvidencePayload(
        source_id=change.source_id,
        evidence_type=_EVIDENCE_TYPE,
        timestamp=change.occurred_at,
        data={"market_state_change": change.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "OBSERVATION",
            "verification_status": "CANONICAL_SOURCE_EVENT",
            "provenance": {
                "chain_id": change.chain.canonical_id,
                "market_id": change.market.canonical_id,
                "source_event_id": change.source_event_id,
                "source_id": change.source_id,
                "source_schema_version": change.schema_version,
            },
        },
    )


@dataclass(frozen=True, slots=True)
class CanonicalMarketStateObservationConsumer:
    """Persist canonical market-state observations without interpreting them."""

    ledger: EvidenceLedger

    def __post_init__(self) -> None:
        if not isinstance(self.ledger, EvidenceLedger):
            raise TypeError("ledger must satisfy EvidenceLedger")

    async def accept(self, change: MarketStateChange) -> str:
        if not isinstance(change, MarketStateChange):
            raise TypeError("change must be a MarketStateChange")

        payload = make_canonical_market_state_observation(change)
        expected_id = payload.get_canonical_id()
        recorded_id = self.ledger.append(payload)
        if recorded_id != expected_id:
            raise RuntimeError("ledger returned a mismatched canonical identity")
        retained = self.ledger.get(expected_id)
        if retained is None or canonicalize(
            retained.canonical_dict()
        ) != canonicalize(payload.canonical_dict()):
            raise RuntimeError("ledger did not retain the canonical observation")
        return change.event_id

__all__ = [
    "CanonicalMarketStateObservationConsumer",
    "make_canonical_market_state_observation",
]
