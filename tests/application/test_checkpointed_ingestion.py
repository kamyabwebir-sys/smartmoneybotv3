from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from smart_money.adapters.evm_v3_provider import EvmV3ShadowProvider
from smart_money.adapters.evm_v3_shadow import (
    DecodedEvmV3PoolEvent,
    EvmV3PoolEventType,
    EvmV3ShadowNormalizer,
)
from smart_money.application.checkpointed_ingestion import (
    CheckpointedIngestionResult,
    CheckpointedIngestionSession,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
)


def _binding():
    chain = ChainId("eip155", "8453")
    token0 = AssetId("USDC", chain, f"0x{'a' * 40}")
    token1 = AssetId("WETH", chain, f"0x{'b' * 40}")
    market = MarketId(VenueId("uniswap-v3"), PairId(token1, token0))
    return EvmV3ShadowNormalizer(
        "evm.shadow.v3",
        chain,
        f"0x{'1' * 40}",
        market,
        token0,
        token1,
    )


def _event(block: int, index: int, marker: str):
    return DecodedEvmV3PoolEvent(
        EvmV3PoolEventType.SWAP,
        f"0x{marker * 64}",
        f"0x{'1' * 40}",
        block,
        index,
        1_700_000_000 + block,
        "100",
        "-1",
    )


def _provider(events, watermarks=None):
    normalizer = _binding()

    def source():
        async def stream():
            for event in events:
                yield event

        return stream()

    def resumable_source(watermark):
        if watermarks is not None:
            watermarks.append(watermark)

        async def stream():
            for event in events:
                if watermark is None or event.block_number >= watermark:
                    yield event

        return stream()

    return EvmV3ShadowProvider(
        normalizer,
        source,
        reorder_window_blocks=2,
        resumable_event_source_factory=resumable_source,
    )


class _MemoryCheckpointStore:
    def __init__(self):
        self.checkpoint = None
        self.saved = []
        self.fail_save = False

    def load(self):
        if self.checkpoint is None:
            raise FileNotFoundError("missing")
        return self.checkpoint

    def save(self, checkpoint):
        if self.fail_save:
            raise OSError("checkpoint save failed")
        self.checkpoint = checkpoint
        self.saved.append(checkpoint)


class _IdempotentConsumer:
    def __init__(self):
        self.accepted = {}
        self.calls = []
        self.fail_on_call = None
        self.wrong_ack = False

    async def accept(self, change):
        self.calls.append(change.event_id)
        if self.fail_on_call == len(self.calls):
            raise RuntimeError("consumer rejected event")
        self.accepted.setdefault(change.event_id, change)
        if self.wrong_ack:
            return "wrong-event-id"
        return change.event_id


@pytest.mark.asyncio
async def test_session_checkpoints_only_after_successful_acknowledgement() -> None:
    events = (_event(100, 0, "a"), _event(100, 1, "b"))
    provider = _provider(events)
    store = _MemoryCheckpointStore()
    consumer = _IdempotentConsumer()
    result = await CheckpointedIngestionSession(
        provider,
        consumer,
        store,
    ).run(provider.normalizer.market)

    assert result.accepted_count == 2
    assert result.first_accepted_event_id == consumer.calls[0]
    assert result.last_accepted_event_id == consumer.calls[1]
    assert result.final_checkpoint_id == store.saved[-1].checkpoint_id
    assert len(store.saved) == 2
    assert not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        result.accepted_count = 3  # type: ignore[misc]


@pytest.mark.asyncio
async def test_consumer_failure_does_not_advance_failed_event_checkpoint() -> None:
    provider = _provider((_event(100, 0, "a"), _event(101, 0, "b")))
    store = _MemoryCheckpointStore()
    consumer = _IdempotentConsumer()
    consumer.fail_on_call = 2
    session = CheckpointedIngestionSession(provider, consumer, store)

    with pytest.raises(RuntimeError, match="rejected"):
        await session.run(provider.normalizer.market)

    assert len(store.saved) == 1
    assert store.saved[0].cursor.ordering_key == (100, 0)


@pytest.mark.asyncio
async def test_wrong_acknowledgement_fails_before_checkpoint_save() -> None:
    provider = _provider((_event(100, 0, "a"),))
    store = _MemoryCheckpointStore()
    consumer = _IdempotentConsumer()
    consumer.wrong_ack = True

    with pytest.raises(ValueError, match="acknowledgement"):
        await CheckpointedIngestionSession(
            provider,
            consumer,
            store,
        ).run(provider.normalizer.market)

    assert store.saved == []


@pytest.mark.asyncio
async def test_checkpoint_save_failure_exposes_at_least_once_boundary() -> None:
    provider = _provider((_event(100, 0, "a"),))
    store = _MemoryCheckpointStore()
    store.fail_save = True
    consumer = _IdempotentConsumer()

    with pytest.raises(OSError, match="save failed"):
        await CheckpointedIngestionSession(
            provider,
            consumer,
            store,
        ).run(provider.normalizer.market)

    assert len(consumer.accepted) == 1
    assert store.checkpoint is None


@pytest.mark.asyncio
async def test_restart_resumes_from_persisted_checkpoint_idempotently() -> None:
    events = (
        _event(100, 0, "a"),
        _event(100, 1, "b"),
        _event(101, 0, "c"),
    )
    watermarks = []
    provider = _provider(events, watermarks)
    store = _MemoryCheckpointStore()
    consumer = _IdempotentConsumer()
    session = CheckpointedIngestionSession(provider, consumer, store)

    first = await session.run(provider.normalizer.market, max_events=2)
    second = await session.run(provider.normalizer.market)

    assert first.accepted_count == 2
    assert second.accepted_count == 1
    assert second.resumed_from_checkpoint_id == first.final_checkpoint_id
    assert len(consumer.accepted) == 3
    assert watermarks == [99]


@pytest.mark.asyncio
async def test_empty_resume_produces_stable_receipt_without_new_checkpoint() -> None:
    provider = _provider((_event(100, 0, "a"),))
    store = _MemoryCheckpointStore()
    consumer = _IdempotentConsumer()
    session = CheckpointedIngestionSession(provider, consumer, store)
    await session.run(provider.normalizer.market)

    first = await session.run(provider.normalizer.market)
    second = await session.run(provider.normalizer.market)

    assert first == second
    assert first.accepted_count == 0
    assert first.final_checkpoint_id == store.checkpoint.checkpoint_id


@pytest.mark.parametrize(
    ("max_events", "error", "message"),
    [
        (0, ValueError, "positive"),
        (-1, ValueError, "positive"),
        (True, TypeError, "integer"),
        (1.5, TypeError, "integer"),
    ],
)
@pytest.mark.asyncio
async def test_session_rejects_invalid_event_limit(
    max_events,
    error,
    message,
) -> None:
    provider = _provider(())
    session = CheckpointedIngestionSession(
        provider,
        _IdempotentConsumer(),
        _MemoryCheckpointStore(),
    )

    with pytest.raises(error, match=message):
        await session.run(
            provider.normalizer.market,
            max_events=max_events,
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"first_accepted_event_id": ""}, "non-empty"),
        ({"final_checkpoint_id": None}, "final_checkpoint_id"),
        ({"resumed_from_checkpoint_id": 1}, "None or non-empty"),
    ],
)
def test_result_rejects_semantically_invalid_identity_payload(
    mutation,
    message,
) -> None:
    payload = {
        "accepted_count": 1,
        "final_checkpoint_id": "checkpoint-1",
        "first_accepted_event_id": "event-1",
        "last_accepted_event_id": "event-1",
        "market_id": "market-1",
        "provider_id": "provider-1",
        "resumed_from_checkpoint_id": None,
        "schema_version": "checkpointed_ingestion_result.v1",
        **mutation,
    }

    with pytest.raises(ValueError, match=message):
        CheckpointedIngestionResult(
            session_id=deterministic_id(
                "checkpointed_ingestion_result",
                payload,
            ),
            provider_id=payload["provider_id"],
            market_id=payload["market_id"],
            resumed_from_checkpoint_id=payload[
                "resumed_from_checkpoint_id"
            ],
            first_accepted_event_id=payload["first_accepted_event_id"],
            last_accepted_event_id=payload["last_accepted_event_id"],
            accepted_count=payload["accepted_count"],
            final_checkpoint_id=payload["final_checkpoint_id"],
        )
