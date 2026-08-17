from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any

from smart_money.core.ids import deterministic_id
from smart_money.domain.market_identity import ChainId, MarketId

_SOURCE_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")


def _normalize_source_id(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("source_id must be a string")
    normalized = value.strip().lower()
    if _SOURCE_PATTERN.fullmatch(normalized) is None:
        raise ValueError("source_id must match canonical source syntax")
    return normalized


def _normalize_source_event_id(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("source_event_id must be a string")
    normalized = value.strip()
    if not normalized or any(character.isspace() for character in normalized):
        raise ValueError("source_event_id must be non-empty without whitespace")
    return normalized


def _require_non_negative_integer(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _to_decimal(value: Decimal | int | str, field_name: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"{field_name} must not be bool or float")
    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, (int, str)):
        result = Decimal(value)
    else:
        raise TypeError(f"{field_name} must be Decimal-compatible")
    if not result.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return result


class MarketStateChangeType(str, Enum):
    SWAP = "swap"
    LIQUIDITY_ADD = "liquidity_add"
    LIQUIDITY_REMOVE = "liquidity_remove"


@dataclass(frozen=True, slots=True)
class MarketStateCursor:
    provider_id: str
    chain: ChainId
    chain_sequence: int
    event_index: int
    schema_version: str = "market_state_cursor.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_id", _normalize_source_id(self.provider_id))
        if not isinstance(self.chain, ChainId):
            raise TypeError("chain must be a ChainId")
        object.__setattr__(
            self,
            "chain_sequence",
            _require_non_negative_integer(self.chain_sequence, "chain_sequence"),
        )
        object.__setattr__(
            self,
            "event_index",
            _require_non_negative_integer(self.event_index, "event_index"),
        )
        if self.schema_version != "market_state_cursor.v1":
            raise ValueError("unsupported MarketStateCursor schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "chain": self.chain.canonical_dict(),
            "chain_sequence": self.chain_sequence,
            "event_index": self.event_index,
            "provider_id": self.provider_id,
            "schema_version": self.schema_version,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("market_state_cursor", self.canonical_dict())

    @property
    def ordering_key(self) -> tuple[int, int]:
        return self.chain_sequence, self.event_index


@dataclass(frozen=True, slots=True)
class MarketStateCheckpoint:
    """Content-addressed resume point for deterministic market-state replay."""

    checkpoint_id: str
    provider_id: str
    chain: ChainId
    market: MarketId
    cursor: MarketStateCursor
    source_watermark: int | None
    reorder_window_blocks: int
    schema_version: str = "market_state_checkpoint.v1"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "provider_id",
            _normalize_source_id(self.provider_id),
        )
        if not isinstance(self.chain, ChainId):
            raise TypeError("chain must be a ChainId")
        if not isinstance(self.market, MarketId):
            raise TypeError("market must be a MarketId")
        if not isinstance(self.cursor, MarketStateCursor):
            raise TypeError("cursor must be a MarketStateCursor")
        if self.source_watermark is not None:
            object.__setattr__(
                self,
                "source_watermark",
                _require_non_negative_integer(
                    self.source_watermark,
                    "source_watermark",
                ),
            )
        object.__setattr__(
            self,
            "reorder_window_blocks",
            _require_non_negative_integer(
                self.reorder_window_blocks,
                "reorder_window_blocks",
            ),
        )
        if self.schema_version != "market_state_checkpoint.v1":
            raise ValueError("unsupported MarketStateCheckpoint schema_version")
        self._validate_binding()
        expected_id = deterministic_id(
            "market_state_checkpoint",
            self.identity_payload(),
        )
        if self.checkpoint_id != expected_id:
            raise ValueError("checkpoint_id does not match deterministic payload")

    def _validate_binding(self) -> None:
        if self.cursor.provider_id != self.provider_id:
            raise ValueError("checkpoint cursor provider_id does not match")
        if self.cursor.chain.canonical_id != self.chain.canonical_id:
            raise ValueError("checkpoint cursor chain does not match")
        for asset in (self.market.pair.base, self.market.pair.quote):
            if asset.chain is None:
                raise ValueError("checkpoint market assets require chain identity")
            if asset.chain.canonical_id != self.chain.canonical_id:
                raise ValueError("checkpoint market chain does not match")
        expected_watermark = (
            None
            if self.cursor.chain_sequence == 0
            else self.cursor.chain_sequence - 1
        )
        if self.source_watermark != expected_watermark:
            raise ValueError("source_watermark is not cursor-safe")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "chain": self.chain.canonical_dict(),
            "cursor": self.cursor.canonical_dict(),
            "market": self.market.canonical_dict(),
            "provider_id": self.provider_id,
            "reorder_window_blocks": self.reorder_window_blocks,
            "schema_version": self.schema_version,
            "source_watermark": self.source_watermark,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"checkpoint_id": self.checkpoint_id, **self.identity_payload()}


def make_market_state_checkpoint(
    *,
    provider_id: str,
    chain: ChainId,
    market: MarketId,
    cursor: MarketStateCursor,
    reorder_window_blocks: int,
) -> MarketStateCheckpoint:
    normalized_provider = _normalize_source_id(provider_id)
    source_watermark = (
        None if cursor.chain_sequence == 0 else cursor.chain_sequence - 1
    )
    payload = {
        "chain": chain.canonical_dict(),
        "cursor": cursor.canonical_dict(),
        "market": market.canonical_dict(),
        "provider_id": normalized_provider,
        "reorder_window_blocks": _require_non_negative_integer(
            reorder_window_blocks,
            "reorder_window_blocks",
        ),
        "schema_version": "market_state_checkpoint.v1",
        "source_watermark": source_watermark,
    }
    return MarketStateCheckpoint(
        checkpoint_id=deterministic_id("market_state_checkpoint", payload),
        provider_id=normalized_provider,
        chain=chain,
        market=market,
        cursor=cursor,
        source_watermark=source_watermark,
        reorder_window_blocks=reorder_window_blocks,
    )


@dataclass(frozen=True, slots=True)
class MarketStateChange:
    """Finalized onchain fact with signed deltas from the pool's perspective."""

    event_id: str
    source_id: str
    source_event_id: str
    chain: ChainId
    market: MarketId
    change_type: MarketStateChangeType
    occurred_at: int
    chain_sequence: int
    event_index: int
    base_delta: Decimal
    quote_delta: Decimal
    liquidity_delta: Decimal
    schema_version: str = "market_state_change.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id must be a non-empty string")
        object.__setattr__(self, "event_id", self.event_id.strip())
        object.__setattr__(self, "source_id", _normalize_source_id(self.source_id))
        object.__setattr__(
            self,
            "source_event_id",
            _normalize_source_event_id(self.source_event_id),
        )
        if not isinstance(self.chain, ChainId):
            raise TypeError("chain must be a ChainId")
        if not isinstance(self.market, MarketId):
            raise TypeError("market must be a MarketId")
        if not isinstance(self.change_type, MarketStateChangeType):
            raise TypeError("change_type must be a MarketStateChangeType")
        object.__setattr__(
            self,
            "occurred_at",
            _require_non_negative_integer(self.occurred_at, "occurred_at"),
        )
        object.__setattr__(
            self,
            "chain_sequence",
            _require_non_negative_integer(self.chain_sequence, "chain_sequence"),
        )
        object.__setattr__(
            self,
            "event_index",
            _require_non_negative_integer(self.event_index, "event_index"),
        )
        for field_name in ("base_delta", "quote_delta", "liquidity_delta"):
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                raise TypeError(f"{field_name} must be Decimal")
            if not value.is_finite():
                raise ValueError(f"{field_name} must be finite")
        if self.schema_version != "market_state_change.v1":
            raise ValueError("unsupported MarketStateChange schema_version")

        self._validate_market_chain()
        self._validate_change_semantics()
        expected_id = deterministic_id("market_state_change", self.identity_payload())
        if self.event_id != expected_id:
            raise ValueError("event_id does not match deterministic payload")

    def _validate_market_chain(self) -> None:
        for asset in (self.market.pair.base, self.market.pair.quote):
            if asset.chain is None:
                raise ValueError("onchain market assets require chain identity")
            if asset.chain.canonical_id != self.chain.canonical_id:
                raise ValueError("market assets must match state-change chain")

    def _validate_change_semantics(self) -> None:
        if self.change_type is MarketStateChangeType.SWAP:
            if self.base_delta == 0 or self.quote_delta == 0:
                raise ValueError("swap deltas must both be non-zero")
            if (self.base_delta > 0) == (self.quote_delta > 0):
                raise ValueError("swap deltas must have opposite signs")
            if self.liquidity_delta != 0:
                raise ValueError("swap liquidity_delta must be zero")
        elif self.change_type is MarketStateChangeType.LIQUIDITY_ADD:
            if self.liquidity_delta <= 0:
                raise ValueError("liquidity-add delta must be positive")
        elif self.liquidity_delta >= 0:
            raise ValueError("liquidity-remove delta must be negative")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "base_delta": self.base_delta,
            "chain": self.chain.canonical_dict(),
            "chain_sequence": self.chain_sequence,
            "change_type": self.change_type,
            "event_index": self.event_index,
            "liquidity_delta": self.liquidity_delta,
            "market": self.market.canonical_dict(),
            "occurred_at": self.occurred_at,
            "quote_delta": self.quote_delta,
            "schema_version": self.schema_version,
            "source_event_id": self.source_event_id,
            "source_id": self.source_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"event_id": self.event_id, **self.identity_payload()}

    @property
    def ordering_key(self) -> tuple[int, int, str]:
        return self.chain_sequence, self.event_index, self.event_id


def make_market_state_change(
    *,
    source_id: str,
    source_event_id: str,
    chain: ChainId,
    market: MarketId,
    change_type: MarketStateChangeType,
    occurred_at: int,
    chain_sequence: int,
    event_index: int,
    base_delta: Decimal | int | str = Decimal("0"),
    quote_delta: Decimal | int | str = Decimal("0"),
    liquidity_delta: Decimal | int | str = Decimal("0"),
) -> MarketStateChange:
    if not isinstance(chain, ChainId):
        raise TypeError("chain must be a ChainId")
    if not isinstance(market, MarketId):
        raise TypeError("market must be a MarketId")
    if not isinstance(change_type, MarketStateChangeType):
        raise TypeError("change_type must be a MarketStateChangeType")

    normalized_source = _normalize_source_id(source_id)
    normalized_event = _normalize_source_event_id(source_event_id)
    normalized_base = _to_decimal(base_delta, "base_delta")
    normalized_quote = _to_decimal(quote_delta, "quote_delta")
    normalized_liquidity = _to_decimal(liquidity_delta, "liquidity_delta")
    payload = {
        "base_delta": normalized_base,
        "chain": chain.canonical_dict(),
        "chain_sequence": _require_non_negative_integer(
            chain_sequence,
            "chain_sequence",
        ),
        "change_type": change_type,
        "event_index": _require_non_negative_integer(event_index, "event_index"),
        "liquidity_delta": normalized_liquidity,
        "market": market.canonical_dict(),
        "occurred_at": _require_non_negative_integer(occurred_at, "occurred_at"),
        "quote_delta": normalized_quote,
        "schema_version": "market_state_change.v1",
        "source_event_id": normalized_event,
        "source_id": normalized_source,
    }
    return MarketStateChange(
        event_id=deterministic_id("market_state_change", payload),
        source_id=normalized_source,
        source_event_id=normalized_event,
        chain=chain,
        market=market,
        change_type=change_type,
        occurred_at=occurred_at,
        chain_sequence=chain_sequence,
        event_index=event_index,
        base_delta=normalized_base,
        quote_delta=normalized_quote,
        liquidity_delta=normalized_liquidity,
    )


__all__ = [
    "MarketStateCheckpoint",
    "MarketStateChange",
    "MarketStateChangeType",
    "MarketStateCursor",
    "make_market_state_checkpoint",
    "make_market_state_change",
]
