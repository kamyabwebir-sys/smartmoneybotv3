from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum

from smart_money.domain.market_identity import AssetId, ChainId, MarketId
from smart_money.domain.market_state import (
    MarketStateChange,
    MarketStateChangeType,
    make_market_state_change,
)

_EVM_ADDRESS_PATTERN = re.compile(r"0x[0-9a-f]{40}")
_TRANSACTION_HASH_PATTERN = re.compile(r"0x[0-9a-f]{64}")


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
        try:
            result = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be Decimal-compatible") from exc
    else:
        raise TypeError(f"{field_name} must be Decimal-compatible")
    if not result.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return result


def _normalize_evm_address(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip().lower()
    if _EVM_ADDRESS_PATTERN.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} must be a 20-byte EVM hex address")
    return normalized


def _normalize_transaction_hash(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("transaction_hash must be a string")
    normalized = value.strip().lower()
    if _TRANSACTION_HASH_PATTERN.fullmatch(normalized) is None:
        raise ValueError("transaction_hash must be a 32-byte EVM hex digest")
    return normalized


def _normalize_provider_id(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("provider_id must be a string")
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("provider_id must be non-empty")
    if not all(
        character.isascii()
        and (character.islower() or character.isdigit() or character in "._-")
        for character in normalized
    ):
        raise ValueError("provider_id must match canonical source syntax")
    return normalized


class EvmV3PoolEventType(str, Enum):
    SWAP = "swap"
    MINT = "mint"
    BURN = "burn"


@dataclass(frozen=True, slots=True)
class DecodedEvmV3PoolEvent:
    """Validated decoded V3 log; no RPC or ABI decoding occurs here."""

    event_type: EvmV3PoolEventType
    transaction_hash: str
    emitter_address: str
    block_number: int
    log_index: int
    block_timestamp: int
    amount0: Decimal | int | str
    amount1: Decimal | int | str
    liquidity_amount: Decimal | int | str = Decimal("0")
    schema_version: str = "decoded_evm_v3_pool_event.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, EvmV3PoolEventType):
            raise TypeError("event_type must be an EvmV3PoolEventType")
        object.__setattr__(
            self,
            "transaction_hash",
            _normalize_transaction_hash(self.transaction_hash),
        )
        object.__setattr__(
            self,
            "emitter_address",
            _normalize_evm_address(self.emitter_address, "emitter_address"),
        )
        object.__setattr__(
            self,
            "block_number",
            _require_non_negative_integer(self.block_number, "block_number"),
        )
        object.__setattr__(
            self,
            "log_index",
            _require_non_negative_integer(self.log_index, "log_index"),
        )
        object.__setattr__(
            self,
            "block_timestamp",
            _require_non_negative_integer(
                self.block_timestamp,
                "block_timestamp",
            ),
        )
        object.__setattr__(
            self,
            "amount0",
            _to_decimal(self.amount0, "amount0"),
        )
        object.__setattr__(
            self,
            "amount1",
            _to_decimal(self.amount1, "amount1"),
        )
        object.__setattr__(
            self,
            "liquidity_amount",
            _to_decimal(self.liquidity_amount, "liquidity_amount"),
        )
        if self.schema_version != "decoded_evm_v3_pool_event.v1":
            raise ValueError("unsupported DecodedEvmV3PoolEvent schema_version")
        self._validate_event_semantics()

    def _validate_event_semantics(self) -> None:
        if self.event_type is EvmV3PoolEventType.SWAP:
            if self.amount0 == 0 or self.amount1 == 0:
                raise ValueError("swap amounts must both be non-zero")
            if (self.amount0 > 0) == (self.amount1 > 0):
                raise ValueError("swap amounts must have opposite signs")
            if self.liquidity_amount != 0:
                raise ValueError("swap liquidity_amount must be zero")
            return

        if self.amount0 < 0 or self.amount1 < 0:
            raise ValueError("mint and burn token amounts must be non-negative")
        if self.amount0 == 0 and self.amount1 == 0:
            raise ValueError("mint and burn require a non-zero token amount")
        if self.liquidity_amount <= 0:
            raise ValueError("mint and burn liquidity_amount must be positive")


@dataclass(frozen=True, slots=True)
class EvmV3ShadowNormalizer:
    """Map decoded V3 pool logs into chain-agnostic market state changes."""

    provider_id: str
    chain: ChainId
    pool_address: str
    market: MarketId
    token0: AssetId
    token1: AssetId

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "provider_id",
            _normalize_provider_id(self.provider_id),
        )
        if not isinstance(self.chain, ChainId):
            raise TypeError("chain must be a ChainId")
        if self.chain.namespace != "eip155":
            raise ValueError("EVM normalizer requires an eip155 chain")
        object.__setattr__(
            self,
            "pool_address",
            _normalize_evm_address(self.pool_address, "pool_address"),
        )
        if not isinstance(self.market, MarketId):
            raise TypeError("market must be a MarketId")
        if not isinstance(self.token0, AssetId) or not isinstance(
            self.token1,
            AssetId,
        ):
            raise TypeError("token0 and token1 must be AssetId")
        self._validate_binding()

    def _validate_binding(self) -> None:
        if self.token0.canonical_id == self.token1.canonical_id:
            raise ValueError("token0 and token1 must be different")
        for token in (self.token0, self.token1):
            if token.chain is None:
                raise ValueError("EVM pool tokens require chain identity")
            if token.chain.canonical_id != self.chain.canonical_id:
                raise ValueError("EVM pool tokens must match normalizer chain")
            if token.contract_address is None:
                raise ValueError("EVM pool tokens require contract addresses")
            _normalize_evm_address(token.contract_address, "token contract_address")

        pool_assets = {
            self.market.pair.base.canonical_id,
            self.market.pair.quote.canonical_id,
        }
        bound_assets = {self.token0.canonical_id, self.token1.canonical_id}
        if pool_assets != bound_assets:
            raise ValueError("token0/token1 must match the market pair")

    def normalize(self, event: DecodedEvmV3PoolEvent) -> MarketStateChange:
        if not isinstance(event, DecodedEvmV3PoolEvent):
            raise TypeError("event must be a DecodedEvmV3PoolEvent")
        if event.emitter_address != self.pool_address:
            raise ValueError("decoded event emitter does not match bound pool")

        base_amount, quote_amount = self._market_ordered_amounts(
            event.amount0,
            event.amount1,
        )
        if event.event_type is EvmV3PoolEventType.SWAP:
            change_type = MarketStateChangeType.SWAP
            liquidity_delta = Decimal("0")
        elif event.event_type is EvmV3PoolEventType.MINT:
            change_type = MarketStateChangeType.LIQUIDITY_ADD
            liquidity_delta = event.liquidity_amount
        else:
            change_type = MarketStateChangeType.LIQUIDITY_REMOVE
            base_amount = -base_amount
            quote_amount = -quote_amount
            liquidity_delta = -event.liquidity_amount

        return make_market_state_change(
            source_id=self.provider_id,
            source_event_id=f"{self.pool_address}:{event.transaction_hash}",
            chain=self.chain,
            market=self.market,
            change_type=change_type,
            occurred_at=event.block_timestamp,
            chain_sequence=event.block_number,
            event_index=event.log_index,
            base_delta=base_amount,
            quote_delta=quote_amount,
            liquidity_delta=liquidity_delta,
        )

    def _market_ordered_amounts(
        self,
        amount0: Decimal,
        amount1: Decimal,
    ) -> tuple[Decimal, Decimal]:
        if self.token0.canonical_id == self.market.pair.base.canonical_id:
            return amount0, amount1
        return amount1, amount0


__all__ = [
    "DecodedEvmV3PoolEvent",
    "EvmV3PoolEventType",
    "EvmV3ShadowNormalizer",
]
