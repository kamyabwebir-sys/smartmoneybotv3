from __future__ import annotations

from dataclasses import FrozenInstanceError

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
from smart_money.application.durable_ingestion_commit import (
    DurableIngestionCommitReceipt,
    create_durable_ingestion_commit_receipt,
)
from smart_money.application.market_state_observation_consumer import (
    CanonicalMarketStateObservationConsumer,
)
from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
)
from smart_money.domain.market_state import (
    MarketStateCheckpoint,
    MarketStateCursor,
    make_market_state_checkpoint,
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


def _event(
    marker: str = "c",
    block: int = 100,
    index: int = 7,
) -> DecodedEvmV3PoolEvent:
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


async def _committed(tmp_path):
    normalizer = _binding()
    event = _event()

    async def source():
        yield event

    provider = EvmV3ShadowProvider(
        normalizer,
        source,
        reorder_window_blocks=2,
    )
    ledger = DurableJsonEvidenceLedger(tmp_path / "evidence.json")
    checkpoint_store = JsonMarketStateCheckpointStore(
        tmp_path / "checkpoint.json"
    )
    result = await CheckpointedIngestionSession(
        provider,
        CanonicalMarketStateObservationConsumer(ledger),
        checkpoint_store,
    ).run(normalizer.market)
    return (
        result,
        normalizer.normalize(event),
        ledger,
        checkpoint_store,
    )


class _StaticCheckpointStore:
    def __init__(self, checkpoint: MarketStateCheckpoint) -> None:
        self.checkpoint = checkpoint

    def load(self) -> MarketStateCheckpoint:
        return self.checkpoint

    def save(self, checkpoint: MarketStateCheckpoint) -> None:
        self.checkpoint = checkpoint


@pytest.mark.asyncio
async def test_receipt_binds_session_evidence_ledger_and_checkpoint(
    tmp_path,
) -> None:
    result, change, ledger, checkpoint_store = await _committed(tmp_path)

    first = create_durable_ingestion_commit_receipt(
        result=result,
        change=change,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )
    second = create_durable_ingestion_commit_receipt(
        result=result,
        change=change,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )

    assert first == second
    assert first.session_id == result.session_id
    assert first.event_id == change.event_id
    assert first.source_event_id == change.source_event_id
    assert first.ledger_content_hash == ledger.content_hash
    assert first.checkpoint_id == result.final_checkpoint_id
    assert first.accepted_count == 1
    assert len(first.ledger_content_hash) == 64
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.accepted_count = 2  # type: ignore[misc]


@pytest.mark.asyncio
async def test_receipt_fails_closed_when_evidence_is_missing(tmp_path) -> None:
    result, change, _, checkpoint_store = await _committed(tmp_path)
    empty_ledger = DurableJsonEvidenceLedger(tmp_path / "empty.json")

    with pytest.raises(ValueError, match="missing from Ledger"):
        create_durable_ingestion_commit_receipt(
            result=result,
            change=change,
            ledger=empty_ledger,
            checkpoint_store=checkpoint_store,
        )


@pytest.mark.asyncio
async def test_receipt_fails_closed_on_result_or_checkpoint_mismatch(
    tmp_path,
) -> None:
    result, change, ledger, checkpoint_store = await _committed(tmp_path)
    different_change = _binding().normalize(_event("d"))

    with pytest.raises(ValueError, match="last event"):
        create_durable_ingestion_commit_receipt(
            result=result,
            change=different_change,
            ledger=ledger,
            checkpoint_store=checkpoint_store,
        )

    checkpoint = checkpoint_store.load()
    different_cursor = MarketStateCursor(
        provider_id=checkpoint.provider_id,
        chain=checkpoint.chain,
        chain_sequence=checkpoint.cursor.chain_sequence + 1,
        event_index=0,
    )
    different_checkpoint = make_market_state_checkpoint(
        provider_id=checkpoint.provider_id,
        chain=checkpoint.chain,
        market=checkpoint.market,
        cursor=different_cursor,
        reorder_window_blocks=checkpoint.reorder_window_blocks,
    )
    with pytest.raises(ValueError, match="checkpoint"):
        create_durable_ingestion_commit_receipt(
            result=result,
            change=change,
            ledger=ledger,
            checkpoint_store=_StaticCheckpointStore(different_checkpoint),
        )


@pytest.mark.asyncio
async def test_receipt_constructor_rejects_forged_identity(tmp_path) -> None:
    result, change, ledger, checkpoint_store = await _committed(tmp_path)
    receipt = create_durable_ingestion_commit_receipt(
        result=result,
        change=change,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )

    with pytest.raises(ValueError, match="receipt_id"):
        DurableIngestionCommitReceipt(
            **{
                **receipt.canonical_dict(),
                "receipt_id": "forged-receipt",
            }
        )
