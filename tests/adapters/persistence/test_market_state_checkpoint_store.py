from __future__ import annotations

import json

import pytest

from smart_money.adapters.evm_v3_provider import EvmV3ShadowProvider
from smart_money.adapters.evm_v3_shadow import (
    DecodedEvmV3PoolEvent,
    EvmV3PoolEventType,
    EvmV3ShadowNormalizer,
)
from smart_money.adapters.persistence.market_state_checkpoint_store import (
    JsonMarketStateCheckpointStore,
)
from smart_money.application.ports.market_state_checkpoint_store import (
    MarketStateCheckpointStore,
)
from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
)


def _checkpoint():
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

    async def empty_source():
        if False:
            yield

    provider = EvmV3ShadowProvider(
        normalizer,
        empty_source,
        reorder_window_blocks=2,
    )
    change = normalizer.normalize(
        DecodedEvmV3PoolEvent(
            EvmV3PoolEventType.SWAP,
            f"0x{'c' * 64}",
            f"0x{'1' * 40}",
            100,
            1,
            1_700_000_100,
            "100",
            "-1",
        )
    )
    return provider.checkpoint_for(change)


def test_checkpoint_round_trip_is_byte_stable_and_satisfies_port(tmp_path) -> None:
    first_path = tmp_path / "first.checkpoint.json"
    second_path = tmp_path / "second.checkpoint.json"
    first_store = JsonMarketStateCheckpointStore(first_path)
    second_store = JsonMarketStateCheckpointStore(second_path)
    checkpoint = _checkpoint()

    assert isinstance(first_store, MarketStateCheckpointStore)
    first_store.save(checkpoint)
    first_bytes = first_path.read_bytes()
    restored = first_store.load()
    second_store.save(restored)
    document = json.loads(first_bytes)

    assert restored == checkpoint
    assert second_path.read_bytes() == first_bytes
    assert document["schema_version"] == "market_state_checkpoint_store.v1"
    assert len(document["content_hash"]) == 64
    assert document["checkpoint"] == checkpoint.canonical_dict()


def test_missing_checkpoint_fails_closed(tmp_path) -> None:
    store = JsonMarketStateCheckpointStore(tmp_path / "missing.json")

    with pytest.raises(FileNotFoundError, match="checkpoint not found"):
        store.load()


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda document: document.pop("content_hash"), "document keys"),
        (lambda document: document.update({"extra": True}), "document keys"),
        (
            lambda document: document.update({"schema_version": "store.v99"}),
            "unsupported",
        ),
        (
            lambda document: document.update({"content_hash": "NOT-A-HASH"}),
            "lowercase SHA-256",
        ),
        (
            lambda document: document["checkpoint"].update({"extra": True}),
            "payload keys",
        ),
        (
            lambda document: document["checkpoint"]["market"].update(
                {"extra": True}
            ),
            "market keys",
        ),
    ],
)
def test_checkpoint_schema_is_strict(
    tmp_path,
    mutation,
    message,
) -> None:
    store = JsonMarketStateCheckpointStore(tmp_path / "strict.json")
    store.save(_checkpoint())
    document = json.loads(store.file_path.read_text(encoding="utf-8"))
    mutation(document)
    store.file_path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        store.load()


def test_checkpoint_tampering_is_detected_by_content_hash(tmp_path) -> None:
    store = JsonMarketStateCheckpointStore(tmp_path / "tampered.json")
    store.save(_checkpoint())
    document = json.loads(store.file_path.read_text(encoding="utf-8"))
    document["checkpoint"]["cursor"]["event_index"] = 2
    store.file_path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        store.load()


def test_forged_checkpoint_is_rejected_with_recomputed_hash(tmp_path) -> None:
    store = JsonMarketStateCheckpointStore(tmp_path / "forged.json")
    store.save(_checkpoint())
    document = json.loads(store.file_path.read_text(encoding="utf-8"))
    document["checkpoint"]["checkpoint_id"] = "forged"
    document["content_hash"] = store._compute_content_hash(
        document["checkpoint"]
    )
    store.file_path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid market-state checkpoint"):
        store.load()


def test_valid_orphaned_temporary_checkpoint_is_recovered(tmp_path) -> None:
    path = tmp_path / "recoverable.json"
    temporary_path = tmp_path / "recoverable.json.tmp"
    store = JsonMarketStateCheckpointStore(path)
    checkpoint = _checkpoint()
    store.save(checkpoint)
    path.replace(temporary_path)

    restored = store.load()

    assert restored == checkpoint
    assert path.is_file()
    assert not temporary_path.exists()


def test_invalid_orphaned_temporary_checkpoint_is_retained(tmp_path) -> None:
    path = tmp_path / "invalid.json"
    temporary_path = tmp_path / "invalid.json.tmp"
    temporary_path.write_text("{not-json", encoding="utf-8")
    store = JsonMarketStateCheckpointStore(path)

    with pytest.raises(ValueError, match="temporary.*recovery failed"):
        store.load()

    assert not path.exists()
    assert temporary_path.is_file()


def test_primary_checkpoint_remains_authoritative(tmp_path) -> None:
    path = tmp_path / "authoritative.json"
    temporary_path = tmp_path / "authoritative.json.tmp"
    store = JsonMarketStateCheckpointStore(path)
    store.save(_checkpoint())
    primary_bytes = path.read_bytes()
    temporary_path.write_text("{not-json", encoding="utf-8")

    restored = store.load()

    assert restored == _checkpoint()
    assert path.read_bytes() == primary_bytes
    assert temporary_path.is_file()
