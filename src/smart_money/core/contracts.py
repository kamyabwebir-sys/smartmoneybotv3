from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from .ids import deterministic_id
from .time import ensure_utc_datetime

_ALLOWED_DIRECTIONS = frozenset({"bullish", "bearish", "neutral"})


def _require_non_empty_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")

    return normalized


def _require_decimal(value: Decimal, field_name: str) -> Decimal:
    if isinstance(value, float):
        raise TypeError(f"{field_name} must be Decimal, not float")

    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal")

    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")

    return value


@dataclass(frozen=True, slots=True)
class Candle:
    """Immutable OHLCV candle contract.

    No wall-clock time, randomness, external I/O, or hidden side effects are used.
    """

    symbol: str
    timeframe: str
    open_time: datetime
    close_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source: str
    schema_version: str = "candle.v1"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_non_empty_text(self.schema_version, "schema_version"),
        )
        object.__setattr__(self, "symbol", _require_non_empty_text(self.symbol, "symbol"))
        object.__setattr__(self, "timeframe", _require_non_empty_text(self.timeframe, "timeframe"))
        object.__setattr__(self, "source", _require_non_empty_text(self.source, "source"))

        open_time = ensure_utc_datetime(self.open_time)
        close_time = ensure_utc_datetime(self.close_time)
        object.__setattr__(self, "open_time", open_time)
        object.__setattr__(self, "close_time", close_time)

        if open_time >= close_time:
            raise ValueError("open_time must be strictly before close_time")

        open_price = _require_decimal(self.open, "open")
        high_price = _require_decimal(self.high, "high")
        low_price = _require_decimal(self.low, "low")
        close_price = _require_decimal(self.close, "close")
        volume = _require_decimal(self.volume, "volume")

        if high_price < max(open_price, close_price, low_price):
            raise ValueError("high must be greater than or equal to open, close, and low")

        if low_price > min(open_price, close_price, high_price):
            raise ValueError("low must be less than or equal to open, close, and high")

        if volume < Decimal("0"):
            raise ValueError("volume must be greater than or equal to zero")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "open_time": self.open_time,
            "close_time": self.close_time,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "source": self.source,
        }

    def deterministic_id(self) -> str:
        return deterministic_id("candle", self.canonical_dict())


@dataclass(frozen=True, slots=True)
class StructureEvent:
    """Immutable future market-structure event contract.

    This model stores event facts only. It does not detect BOS, CHOCH, sweeps,
    imbalances, setups, decisions, alerts, or any trading action.
    """

    event_type: str
    symbol: str
    timeframe: str
    event_time: datetime
    price: Decimal
    direction: str
    source_candle_id: str
    evidence_ids: tuple[str, ...]
    rule_id: str
    rule_version: str
    schema_version: str = "structure_event.v1"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_non_empty_text(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "event_type",
            _require_non_empty_text(self.event_type, "event_type"),
        )
        object.__setattr__(self, "symbol", _require_non_empty_text(self.symbol, "symbol"))
        object.__setattr__(self, "timeframe", _require_non_empty_text(self.timeframe, "timeframe"))
        object.__setattr__(
            self,
            "source_candle_id",
            _require_non_empty_text(self.source_candle_id, "source_candle_id"),
        )
        object.__setattr__(self, "rule_id", _require_non_empty_text(self.rule_id, "rule_id"))
        object.__setattr__(
            self,
            "rule_version",
            _require_non_empty_text(self.rule_version, "rule_version"),
        )

        object.__setattr__(self, "event_time", ensure_utc_datetime(self.event_time))
        _require_decimal(self.price, "price")

        direction = _require_non_empty_text(self.direction, "direction")
        if direction not in _ALLOWED_DIRECTIONS:
            raise ValueError("direction must be one of: bullish, bearish, neutral")
        object.__setattr__(self, "direction", direction)

        if not isinstance(self.evidence_ids, tuple):
            raise TypeError("evidence_ids must be a tuple")

        normalized_evidence_ids: list[str] = []
        for evidence_id in self.evidence_ids:
            normalized_evidence_ids.append(_require_non_empty_text(evidence_id, "evidence_ids"))

        object.__setattr__(self, "evidence_ids", tuple(sorted(normalized_evidence_ids)))

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_type": self.event_type,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "event_time": self.event_time,
            "price": self.price,
            "direction": self.direction,
            "source_candle_id": self.source_candle_id,
            "evidence_ids": self.evidence_ids,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
        }

    def deterministic_id(self) -> str:
        return deterministic_id("structure_event", self.canonical_dict())
