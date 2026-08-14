from __future__ import annotations

import re
from dataclasses import dataclass

from smart_money.core.ids import deterministic_id

_SYMBOL_PATTERN = re.compile(r"[A-Z0-9][A-Z0-9._-]{0,31}")
_SLUG_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")
_REFERENCE_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")


def normalize_symbol(value: str) -> str:
    """Return the canonical ASCII asset symbol."""
    if not isinstance(value, str):
        raise TypeError("symbol must be a string")
    normalized = value.strip().upper()
    if _SYMBOL_PATTERN.fullmatch(normalized) is None:
        raise ValueError("symbol must match canonical asset symbol syntax")
    return normalized


def _normalize_slug(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip().lower()
    if _SLUG_PATTERN.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} must match canonical slug syntax")
    return normalized


def _normalize_reference(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("chain reference must be a string")
    normalized = value.strip().lower()
    if _REFERENCE_PATTERN.fullmatch(normalized) is None:
        raise ValueError("chain reference must match canonical reference syntax")
    return normalized


@dataclass(frozen=True, slots=True)
class ChainId:
    namespace: str
    reference: str
    schema_version: str = "chain_id.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "namespace", _normalize_slug(self.namespace, "namespace"))
        object.__setattr__(self, "reference", _normalize_reference(self.reference))
        if self.schema_version != "chain_id.v1":
            raise ValueError("unsupported ChainId schema_version")

    def canonical_dict(self) -> dict[str, str]:
        return {
            "namespace": self.namespace,
            "reference": self.reference,
            "schema_version": self.schema_version,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("chain", self.canonical_dict())


@dataclass(frozen=True, slots=True)
class VenueId:
    venue: str
    schema_version: str = "venue_id.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "venue", _normalize_slug(self.venue, "venue"))
        if self.schema_version != "venue_id.v1":
            raise ValueError("unsupported VenueId schema_version")

    def canonical_dict(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "venue": self.venue,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("venue", self.canonical_dict())


@dataclass(frozen=True, slots=True)
class AssetId:
    symbol: str
    chain: ChainId | None = None
    contract_address: str | None = None
    schema_version: str = "asset_id.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", normalize_symbol(self.symbol))
        if self.chain is not None and not isinstance(self.chain, ChainId):
            raise TypeError("chain must be a ChainId or None")
        if self.contract_address is not None:
            if self.chain is None:
                raise ValueError("contract_address requires chain identity")
            if not isinstance(self.contract_address, str):
                raise TypeError("contract_address must be a string")
            normalized_address = self.contract_address.strip()
            contains_whitespace = any(
                character.isspace() for character in normalized_address
            )
            if not normalized_address or contains_whitespace:
                raise ValueError("contract_address must be non-empty without whitespace")
            if self.chain.namespace == "eip155":
                normalized_address = normalized_address.lower()
            object.__setattr__(self, "contract_address", normalized_address)
        if self.schema_version != "asset_id.v1":
            raise ValueError("unsupported AssetId schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "chain": None if self.chain is None else self.chain.canonical_dict(),
            "contract_address": self.contract_address,
            "schema_version": self.schema_version,
            "symbol": self.symbol,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("asset", self.canonical_dict())


@dataclass(frozen=True, slots=True)
class PairId:
    base: AssetId
    quote: AssetId
    schema_version: str = "pair_id.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.base, AssetId):
            raise TypeError("base must be an AssetId")
        if not isinstance(self.quote, AssetId):
            raise TypeError("quote must be an AssetId")
        if self.base.canonical_id == self.quote.canonical_id:
            raise ValueError("base and quote assets must be different")
        if self.schema_version != "pair_id.v1":
            raise ValueError("unsupported PairId schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "base": self.base.canonical_dict(),
            "quote": self.quote.canonical_dict(),
            "schema_version": self.schema_version,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("pair", self.canonical_dict())


@dataclass(frozen=True, slots=True)
class MarketId:
    venue: VenueId
    pair: PairId
    schema_version: str = "market_id.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.venue, VenueId):
            raise TypeError("venue must be a VenueId")
        if not isinstance(self.pair, PairId):
            raise TypeError("pair must be a PairId")
        if self.schema_version != "market_id.v1":
            raise ValueError("unsupported MarketId schema_version")

    def canonical_dict(self) -> dict[str, object]:
        return {
            "pair": self.pair.canonical_dict(),
            "schema_version": self.schema_version,
            "venue": self.venue.canonical_dict(),
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("market", self.canonical_dict())


__all__ = [
    "AssetId",
    "ChainId",
    "MarketId",
    "PairId",
    "VenueId",
    "normalize_symbol",
]
