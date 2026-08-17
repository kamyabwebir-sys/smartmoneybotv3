from __future__ import annotations

from pathlib import Path

import pytest

from smart_money.adapters.evm_v3_provider import EvmV3ShadowProvider
from smart_money.adapters.evm_v3_shadow import (
    DecodedEvmV3PoolEvent,
    EvmV3PoolEventType,
    EvmV3ShadowNormalizer,
)
from smart_money.adapters.persistence.durable_json_ledger import (
    DurableJsonEvidenceLedger,
)
from smart_money.adapters.persistence.market_state_checkpoint_store import (
    JsonMarketStateCheckpointStore,
)
from smart_money.application.checkpointed_ingestion import (
    CheckpointedIngestionSession,
)
from smart_money.application.market_state_observation_consumer import (
    CanonicalMarketStateObservationConsumer,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
)


def _event(block: int, index: int, marker: str) -> DecodedEvmV3PoolEvent:
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


def _provider(
    events: tuple[DecodedEvmV3PoolEvent, ...],
) -> EvmV3ShadowProvider:
    chain = ChainId("eip155", "8453")
    token0 = AssetId("USDC", chain, f"0x{'a' * 40}")
    token1 = AssetId("WETH", chain, f"0x{'b' * 40}")
    market = MarketId(VenueId("uniswap-v3"), PairId(token1, token0))
    normalizer = EvmV3ShadowNormalizer(
        "evm.shadow.v3",
        chain,
        f"0x{'1' * 40}",
        market,
        token0,
        token1,
    )

    async def source():
        for event in events:
            yield event

    def resumable_source(watermark: int | None):
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


def _session(
    provider: EvmV3ShadowProvider,
    ledger_path: Path,
    checkpoint_path: Path,
) -> tuple[CheckpointedIngestionSession, DurableJsonEvidenceLedger]:
    ledger = DurableJsonEvidenceLedger(ledger_path)
    consumer = CanonicalMarketStateObservationConsumer(ledger)
    store = JsonMarketStateCheckpointStore(checkpoint_path)
    return CheckpointedIngestionSession(provider, consumer, store), ledger


class _FailingCheckpointStore:
    def __init__(self, delegate: JsonMarketStateCheckpointStore) -> None:
        self.delegate = delegate

    def load(self):
        return self.delegate.load()

    def save(self, checkpoint) -> None:
        raise OSError("checkpoint persistence failed")


@pytest.mark.asyncio
async def test_durable_ledger_satisfies_port_and_duplicate_is_byte_stable(
    tmp_path,
) -> None:
    ledger_path = tmp_path / "evidence.json"
    provider = _provider((_event(100, 0, "a"),))
    change = provider.normalizer.normalize(_event(100, 0, "a"))
    consumer = CanonicalMarketStateObservationConsumer(
        DurableJsonEvidenceLedger(ledger_path)
    )

    first_id = await consumer.accept(change)
    first_bytes = ledger_path.read_bytes()
    second_id = await consumer.accept(change)

    restored = DurableJsonEvidenceLedger(ledger_path)
    assert isinstance(restored, EvidenceLedger)
    assert first_id == second_id == change.event_id
    assert restored.entry_count == 1
    assert ledger_path.read_bytes() == first_bytes


@pytest.mark.asyncio
async def test_ingestion_persists_evidence_before_checkpoint_and_resumes(
    tmp_path,
) -> None:
    events = (
        _event(100, 0, "a"),
        _event(100, 1, "b"),
        _event(101, 0, "c"),
    )
    provider = _provider(events)
    ledger_path = tmp_path / "evidence.json"
    checkpoint_path = tmp_path / "checkpoint.json"
    first_session, first_ledger = _session(
        provider,
        ledger_path,
        checkpoint_path,
    )

    first = await first_session.run(
        provider.normalizer.market,
        max_events=2,
    )
    second_session, second_ledger = _session(
        provider,
        ledger_path,
        checkpoint_path,
    )
    second = await second_session.run(provider.normalizer.market)
    stable_ledger_bytes = ledger_path.read_bytes()
    stable_checkpoint_bytes = checkpoint_path.read_bytes()
    third_session, third_ledger = _session(
        provider,
        ledger_path,
        checkpoint_path,
    )
    third = await third_session.run(provider.normalizer.market)

    assert first.accepted_count == 2
    assert first_ledger.entry_count == 2
    assert second.accepted_count == 1
    assert second.resumed_from_checkpoint_id == first.final_checkpoint_id
    assert second_ledger.entry_count == 3
    assert third.accepted_count == 0
    assert third_ledger.entry_count == 3
    assert ledger_path.read_bytes() == stable_ledger_bytes
    assert checkpoint_path.read_bytes() == stable_checkpoint_bytes


@pytest.mark.asyncio
async def test_ledger_write_failure_does_not_advance_checkpoint(tmp_path) -> None:
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("blocked", encoding="utf-8")
    ledger_path = blocked_parent / "evidence.json"
    checkpoint_path = tmp_path / "checkpoint.json"
    provider = _provider((_event(100, 0, "a"),))
    session, ledger = _session(provider, ledger_path, checkpoint_path)

    with pytest.raises(OSError):
        await session.run(provider.normalizer.market)

    assert ledger.entry_count == 0
    assert not checkpoint_path.exists()


@pytest.mark.asyncio
async def test_checkpoint_failure_replays_durable_evidence_idempotently(
    tmp_path,
) -> None:
    provider = _provider((_event(100, 0, "a"),))
    ledger_path = tmp_path / "evidence.json"
    checkpoint_path = tmp_path / "checkpoint.json"
    ledger = DurableJsonEvidenceLedger(ledger_path)
    consumer = CanonicalMarketStateObservationConsumer(ledger)
    checkpoint_store = JsonMarketStateCheckpointStore(checkpoint_path)
    failing_session = CheckpointedIngestionSession(
        provider,
        consumer,
        _FailingCheckpointStore(checkpoint_store),
    )

    with pytest.raises(OSError, match="checkpoint persistence failed"):
        await failing_session.run(provider.normalizer.market)

    durable_bytes = ledger_path.read_bytes()
    assert ledger.entry_count == 1
    assert not checkpoint_path.exists()

    resumed_session, restored_ledger = _session(
        provider,
        ledger_path,
        checkpoint_path,
    )
    result = await resumed_session.run(provider.normalizer.market)

    assert result.accepted_count == 1
    assert restored_ledger.entry_count == 1
    assert ledger_path.read_bytes() == durable_bytes
    assert checkpoint_path.is_file()
