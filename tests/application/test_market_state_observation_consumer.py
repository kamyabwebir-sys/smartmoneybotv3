from __future__ import annotations

from collections.abc import Iterator
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from smart_money.application.market_state_observation_consumer import (
    CanonicalMarketStateObservationConsumer,
)
from smart_money.application.ports.market_state_ingestion import (
    IdempotentMarketStateConsumer,
)
from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
)
from smart_money.domain.market_state import (
    MarketStateChange,
    MarketStateChangeType,
    make_market_state_change,
)
from smart_money.ingestion.contracts import EvidencePayload
from smart_money.ingestion.ledger import EvidenceGroundingLedger


def _change() -> MarketStateChange:
    chain = ChainId("eip155", "8453")
    base = AssetId("WETH", chain, f"0x{'a' * 40}")
    quote = AssetId("USDC", chain, f"0x{'b' * 40}")
    market = MarketId(VenueId("uniswap-v3"), PairId(base, quote))
    return make_market_state_change(
        source_id="evm.shadow.v3",
        source_event_id=f"0x{'c' * 64}:7",
        chain=chain,
        market=market,
        change_type=MarketStateChangeType.SWAP,
        occurred_at=1_700_000_123,
        chain_sequence=12_345,
        event_index=7,
        base_delta=Decimal("1.2300"),
        quote_delta=Decimal("-456.7800"),
    )


@pytest.mark.asyncio
async def test_consumer_persists_canonical_observation_and_acknowledges_event() -> None:
    change = _change()
    ledger = EvidenceGroundingLedger()
    consumer = CanonicalMarketStateObservationConsumer(ledger)

    acknowledged_id = await consumer.accept(change)

    assert acknowledged_id == change.event_id
    assert ledger.entry_count == 1
    payload = next(ledger.iter_payloads())
    assert payload.source_id == change.source_id
    assert payload.evidence_type == "canonical_market_state_observation"
    assert payload.timestamp == change.occurred_at
    assert payload.data["market_state_change"] == change.canonical_dict()
    assert payload.metadata == {
        "authority": "NONE",
        "classification": "OBSERVATION",
        "provenance": {
            "chain_id": change.chain.canonical_id,
            "market_id": change.market.canonical_id,
            "source_event_id": change.source_event_id,
            "source_id": change.source_id,
            "source_schema_version": change.schema_version,
        },
        "verification_status": "CANONICAL_SOURCE_EVENT",
    }


@pytest.mark.asyncio
async def test_projection_is_deterministic_immutable_and_idempotent() -> None:
    change = _change()
    ledger = EvidenceGroundingLedger()
    consumer = CanonicalMarketStateObservationConsumer(ledger)

    first_ack = await consumer.accept(change)
    first_payload = next(ledger.iter_payloads())
    second_ack = await consumer.accept(change)
    second_payload = next(ledger.iter_payloads())

    assert first_ack == second_ack == change.event_id
    assert first_payload == second_payload
    assert first_payload.get_canonical_id() == second_payload.get_canonical_id()
    assert ledger.entry_count == 1
    assert not hasattr(consumer, "__dict__")
    with pytest.raises(FrozenInstanceError):
        consumer.ledger = EvidenceGroundingLedger()  # type: ignore[misc]
    with pytest.raises(TypeError):
        first_payload.data["event_id"] = "changed"  # type: ignore[index]


class _BrokenLedger:
    def __init__(self, *, mismatched_id: bool = False) -> None:
        self.payload: EvidencePayload | None = None
        self.mismatched_id = mismatched_id

    def append(self, payload: EvidencePayload) -> str:
        if not self.mismatched_id:
            self.payload = payload
        return (
            "mismatched-id"
            if self.mismatched_id
            else payload.get_canonical_id()
        )

    def contains(self, canonical_id: str) -> bool:
        return False

    def get(self, canonical_id: str) -> EvidencePayload | None:
        return None

    def iter_payloads(self) -> Iterator[EvidencePayload]:
        return iter(())

    @property
    def entry_count(self) -> int:
        return 0


@pytest.mark.parametrize(
    ("ledger", "message"),
    [
        (_BrokenLedger(mismatched_id=True), "mismatched canonical identity"),
        (_BrokenLedger(), "did not retain"),
    ],
)
@pytest.mark.asyncio
async def test_consumer_fails_closed_on_ledger_acceptance_violation(
    ledger: _BrokenLedger,
    message: str,
) -> None:
    consumer = CanonicalMarketStateObservationConsumer(ledger)

    with pytest.raises(RuntimeError, match=message):
        await consumer.accept(_change())


@pytest.mark.asyncio
async def test_consumer_satisfies_port_and_rejects_invalid_inputs() -> None:
    consumer = CanonicalMarketStateObservationConsumer(EvidenceGroundingLedger())

    assert isinstance(consumer, IdempotentMarketStateConsumer)
    with pytest.raises(TypeError, match="MarketStateChange"):
        await consumer.accept("not-a-change")  # type: ignore[arg-type]
