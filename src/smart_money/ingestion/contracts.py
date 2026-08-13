from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping

from smart_money.core.ids import deterministic_id


def _require_non_empty_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


def _to_decimal(value: Decimal | int | float | str, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be numeric")

    if isinstance(value, Decimal):
        result = value
    elif isinstance(value, (int, float, str)):
        result = Decimal(str(value))
    else:
        raise TypeError(f"{field_name} must be Decimal-compatible")

    if not result.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return result


def _freeze(value: Any, field_name: str) -> Any:
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key in value:
            if not isinstance(key, str) or not key.strip():
                raise TypeError(f"{field_name} keys must be non-empty strings")
            normalized_key = key.strip()
            if normalized_key in frozen:
                raise ValueError(f"{field_name} contains duplicate normalized keys")
            frozen[normalized_key] = _freeze(
                value[key], f"{field_name}.{normalized_key}"
            )
        return MappingProxyType(dict(sorted(frozen.items())))

    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item, field_name) for item in value)

    if isinstance(value, (str, int, bool, Decimal, datetime)) or value is None:
        return value

    if isinstance(value, float):
        return _to_decimal(value, field_name)

    raise TypeError(
        f"{field_name} contains unsupported value type: {type(value).__name__}"
    )


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class EvidencePayload:
    """Immutable, content-addressed evidence accepted by the ingestion boundary."""

    source_id: str
    evidence_type: str = "generic"
    timestamp: int = 0
    data: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str):
            raise TypeError("source_id must be a string")
        if not isinstance(self.evidence_type, str):
            raise TypeError("evidence_type must be a string")
        object.__setattr__(self, "source_id", self.source_id.strip())
        object.__setattr__(self, "evidence_type", self.evidence_type.strip())

        if isinstance(self.timestamp, bool) or not isinstance(self.timestamp, int):
            raise TypeError("timestamp must be an integer")
        if not isinstance(self.data, Mapping):
            raise TypeError("data must be a mapping")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(self, "data", _freeze(self.data, "data"))
        object.__setattr__(self, "metadata", _freeze(self.metadata, "metadata"))

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "evidence_type": self.evidence_type,
            "timestamp": self.timestamp,
            "data": _plain(self.data),
            "metadata": _plain(self.metadata),
        }

    def get_canonical_id(self) -> str:
        return deterministic_id("evidence", self.canonical_dict())


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Deterministic status of an ingestion attempt."""

    accepted: bool
    canonical_id: str
    message: str = ""


@dataclass(frozen=True, slots=True)
class IngestionCandle:
    """Provider-facing candle before conversion to the strict core contract."""

    timestamp: int | datetime
    open: Decimal | int | float | str
    high: Decimal | int | float | str
    low: Decimal | int | float | str
    close: Decimal | int | float | str
    volume: Decimal | int | float | str
    symbol: str = ""
    interval: str = ""
    source_id: str = ""
    is_final: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.timestamp, bool) or not isinstance(
            self.timestamp, (int, datetime)
        ):
            raise TypeError("timestamp must be an integer or datetime")

        open_price = _to_decimal(self.open, "open")
        high_price = _to_decimal(self.high, "high")
        low_price = _to_decimal(self.low, "low")
        close_price = _to_decimal(self.close, "close")
        volume = _to_decimal(self.volume, "volume")

        if high_price < max(open_price, close_price, low_price):
            raise ValueError(
                "high must be greater than or equal to open, close, and low"
            )
        if low_price > min(open_price, close_price, high_price):
            raise ValueError("low must be less than or equal to open, close, and high")
        if volume < 0:
            raise ValueError("volume must be non-negative")

        object.__setattr__(self, "open", open_price)
        object.__setattr__(self, "high", high_price)
        object.__setattr__(self, "low", low_price)
        object.__setattr__(self, "close", close_price)
        object.__setattr__(self, "volume", volume)


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """Immutable point-in-time provider snapshot."""

    symbol: str
    price: Decimal | int | float | str
    extra_metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "symbol", _require_non_empty_text(self.symbol, "symbol")
        )
        object.__setattr__(self, "price", _to_decimal(self.price, "price"))
        if not isinstance(self.extra_metadata, Mapping):
            raise TypeError("extra_metadata must be a mapping")
        object.__setattr__(
            self,
            "extra_metadata",
            _freeze(self.extra_metadata, "extra_metadata"),
        )
