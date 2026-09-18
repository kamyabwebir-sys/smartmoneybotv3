# install_slice_0_6.ps1
# Installs Slice 0.6 - domain contracts, canonical serialization, deterministic IDs.

param(
    [string]$ProjectRoot = ".",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[Slice 0.6] $Message" -ForegroundColor Cyan
}

function New-DirectoryIfMissing {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Write-TextFile {
    param(
        [string]$Path,
        [string]$Content
    )

    if ((Test-Path -LiteralPath $Path) -and (-not $Force)) {
        Write-Host "SKIP existing file: $Path" -ForegroundColor Yellow
        return
    }

    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-DirectoryIfMissing -Path $parent
    }

    Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
    Write-Host "WRITE $Path" -ForegroundColor Green
}

$Root = Resolve-Path $ProjectRoot
$RootPath = $Root.Path

Write-Step "Installing into: $RootPath"

New-DirectoryIfMissing -Path (Join-Path $RootPath "src\smart_money\core")
New-DirectoryIfMissing -Path (Join-Path $RootPath "tests")
New-DirectoryIfMissing -Path (Join-Path $RootPath "docs")
New-DirectoryIfMissing -Path (Join-Path $RootPath "scripts")

Write-Step "Writing package files"

Write-TextFile -Path (Join-Path $RootPath "src\smart_money\__init__.py") -Content @'
"""Smart Money deterministic market-structure platform."""
'@

Write-TextFile -Path (Join-Path $RootPath "src\smart_money\core\__init__.py") -Content @'
"""Pure deterministic core for Smart Money market-structure analysis."""

from .contracts import Candle, StructureEvent
from .ids import deterministic_id
from .serialization import canonical_json, canonicalize
from .time import datetime_to_canonical, ensure_utc_datetime

__all__ = [
    "Candle",
    "StructureEvent",
    "canonical_json",
    "canonicalize",
    "datetime_to_canonical",
    "deterministic_id",
    "ensure_utc_datetime",
]
'@

Write-TextFile -Path (Join-Path $RootPath "src\smart_money\core\time.py") -Content @'
from __future__ import annotations

from datetime import datetime, timezone


def ensure_utc_datetime(value: datetime) -> datetime:
    """Return an aware UTC datetime or raise ValueError.

    This function intentionally never reads wall-clock time.
    """
    if not isinstance(value, datetime):
        raise TypeError("value must be a datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")

    return value.astimezone(timezone.utc)


def datetime_to_canonical(value: datetime) -> str:
    """Serialize a datetime as canonical UTC ISO-8601 with Z suffix."""
    utc_value = ensure_utc_datetime(value)

    if utc_value.microsecond:
        text = utc_value.isoformat(timespec="microseconds")
    else:
        text = utc_value.isoformat(timespec="seconds")

    return text.replace("+00:00", "Z")
'@

Write-TextFile -Path (Join-Path $RootPath "src\smart_money\core\serialization.py") -Content @'
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from collections.abc import Mapping, Sequence
from typing import Any

from .time import datetime_to_canonical


def _decimal_to_canonical(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("Decimal values must be finite")
    return format(value.normalize(), "f")


def canonicalize(value: Any) -> Any:
    """Convert supported values into canonical JSON-compatible values."""
    if is_dataclass(value):
        return canonicalize(asdict(value))

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise TypeError("canonical dict keys must be strings")
            normalized[key] = canonicalize(value[key])
        return normalized

    if isinstance(value, tuple):
        return [canonicalize(item) for item in value]

    if isinstance(value, list):
        return [canonicalize(item) for item in value]

    if isinstance(value, datetime):
        return datetime_to_canonical(value)

    if isinstance(value, Decimal):
        return _decimal_to_canonical(value)

    if isinstance(value, Enum):
        return canonicalize(value.value)

    if isinstance(value, float):
        raise TypeError("float values are not allowed in canonical identity serialization")

    if value is None or isinstance(value, str | int | bool):
        return value

    raise TypeError(f"unsupported value for canonical serialization: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    """Return deterministic canonical JSON.

    JSON keys are sorted and separators are fixed to make hashing stable.
    """
    return json.dumps(
        canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
'@

Write-TextFile -Path (Join-Path $RootPath "src\smart_money\core\ids.py") -Content @'
from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from .serialization import canonical_json


def deterministic_id(namespace: str, payload: Mapping[str, Any]) -> str:
    """Build a deterministic ID from namespace and canonical payload."""
    if not isinstance(namespace, str) or not namespace.strip():
        raise ValueError("namespace must be a non-empty string")

    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")

    encoded = canonical_json(payload).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:32]
    return f"{namespace.strip()}_{digest}"
'@

Write-TextFile -Path (Join-Path $RootPath "src\smart_money\core\contracts.py") -Content @'
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
        object.__setattr__(self, "schema_version", _require_non_empty_text(self.schema_version, "schema_version"))
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
        object.__setattr__(self, "schema_version", _require_non_empty_text(self.schema_version, "schema_version"))
        object.__setattr__(self, "event_type", _require_non_empty_text(self.event_type, "event_type"))
        object.__setattr__(self, "symbol", _require_non_empty_text(self.symbol, "symbol"))
        object.__setattr__(self, "timeframe", _require_non_empty_text(self.timeframe, "timeframe"))
        object.__setattr__(self, "source_candle_id", _require_non_empty_text(self.source_candle_id, "source_candle_id"))
        object.__setattr__(self, "rule_id", _require_non_empty_text(self.rule_id, "rule_id"))
        object.__setattr__(self, "rule_version", _require_non_empty_text(self.rule_version, "rule_version"))

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
'@

Write-Step "Writing tests"

Write-TextFile -Path (Join-Path $RootPath "tests\test_contract_candle.py") -Content @'
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from smart_money.core.contracts import Candle


def _valid_candle() -> Candle:
    return Candle(
        symbol="SOLUSDT",
        timeframe="1m",
        open_time=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        close_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
        open=Decimal("100.00"),
        high=Decimal("105.00"),
        low=Decimal("99.00"),
        close=Decimal("101.00"),
        volume=Decimal("1234.50"),
        source="fixture",
    )


def test_valid_candle_can_be_created() -> None:
    candle = _valid_candle()
    assert candle.symbol == "SOLUSDT"
    assert candle.schema_version == "candle.v1"


def test_candle_is_immutable() -> None:
    candle = _valid_candle()
    with pytest.raises(FrozenInstanceError):
        candle.symbol = "BTCUSDT"  # type: ignore[misc]


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Candle(
            symbol="SOLUSDT",
            timeframe="1m",
            open_time=datetime(2024, 1, 1, 0, 0),
            close_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("1"),
            source="fixture",
        )


def test_open_time_must_be_before_close_time() -> None:
    timestamp = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="open_time"):
        Candle(
            symbol="SOLUSDT",
            timeframe="1m",
            open_time=timestamp,
            close_time=timestamp,
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("1"),
            source="fixture",
        )


def test_float_price_is_rejected() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        Candle(
            symbol="SOLUSDT",
            timeframe="1m",
            open_time=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
            close_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            open=100.0,  # type: ignore[arg-type]
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("1"),
            source="fixture",
        )


def test_invalid_ohlc_relationship_is_rejected() -> None:
    with pytest.raises(ValueError, match="high"):
        Candle(
            symbol="SOLUSDT",
            timeframe="1m",
            open_time=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
            close_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            open=Decimal("100"),
            high=Decimal("99"),
            low=Decimal("98"),
            close=Decimal("100"),
            volume=Decimal("1"),
            source="fixture",
        )


def test_negative_volume_is_rejected() -> None:
    with pytest.raises(ValueError, match="volume"):
        Candle(
            symbol="SOLUSDT",
            timeframe="1m",
            open_time=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
            close_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("-1"),
            source="fixture",
        )


def test_canonical_dict_is_stable() -> None:
    candle = _valid_candle()
    assert list(candle.canonical_dict().keys()) == [
        "schema_version",
        "symbol",
        "timeframe",
        "open_time",
        "close_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "source",
    ]


def test_deterministic_id_is_stable_across_equivalent_objects() -> None:
    assert _valid_candle().deterministic_id() == _valid_candle().deterministic_id()
'@

Write-TextFile -Path (Join-Path $RootPath "tests\test_contract_structure_event.py") -Content @'
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from smart_money.core.contracts import StructureEvent


def _valid_event(evidence_ids: tuple[str, ...] = ("ev_b", "ev_a")) -> StructureEvent:
    return StructureEvent(
        event_type="placeholder_structure_event",
        symbol="SOLUSDT",
        timeframe="1m",
        event_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
        price=Decimal("101.00"),
        direction="bullish",
        source_candle_id="candle_abc",
        evidence_ids=evidence_ids,
        rule_id="rule.placeholder",
        rule_version="v1",
    )


def test_valid_event_can_be_created() -> None:
    event = _valid_event()
    assert event.event_type == "placeholder_structure_event"


def test_event_is_immutable() -> None:
    event = _valid_event()
    with pytest.raises(FrozenInstanceError):
        event.direction = "bearish"  # type: ignore[misc]


def test_naive_event_time_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        StructureEvent(
            event_type="placeholder",
            symbol="SOLUSDT",
            timeframe="1m",
            event_time=datetime(2024, 1, 1, 0, 1),
            price=Decimal("101"),
            direction="bullish",
            source_candle_id="candle_abc",
            evidence_ids=("ev_a",),
            rule_id="rule.placeholder",
            rule_version="v1",
        )


def test_invalid_direction_is_rejected() -> None:
    with pytest.raises(ValueError, match="direction"):
        _valid_event().__class__(
            event_type="placeholder",
            symbol="SOLUSDT",
            timeframe="1m",
            event_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            price=Decimal("101"),
            direction="up",
            source_candle_id="candle_abc",
            evidence_ids=("ev_a",),
            rule_id="rule.placeholder",
            rule_version="v1",
        )


def test_float_price_is_rejected() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        StructureEvent(
            event_type="placeholder",
            symbol="SOLUSDT",
            timeframe="1m",
            event_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            price=101.0,  # type: ignore[arg-type]
            direction="bullish",
            source_candle_id="candle_abc",
            evidence_ids=("ev_a",),
            rule_id="rule.placeholder",
            rule_version="v1",
        )


def test_evidence_ids_list_is_rejected() -> None:
    with pytest.raises(TypeError, match="tuple"):
        StructureEvent(
            event_type="placeholder",
            symbol="SOLUSDT",
            timeframe="1m",
            event_time=datetime(2024, 1, 1, 0, 1, tzinfo=timezone.utc),
            price=Decimal("101"),
            direction="bullish",
            source_candle_id="candle_abc",
            evidence_ids=["ev_a"],  # type: ignore[arg-type]
            rule_id="rule.placeholder",
            rule_version="v1",
        )


def test_empty_evidence_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="evidence_ids"):
        _valid_event(evidence_ids=("ev_a", " "))


def test_evidence_ids_are_canonically_sorted() -> None:
    assert _valid_event().evidence_ids == ("ev_a", "ev_b")


def test_deterministic_id_is_stable_when_evidence_order_differs() -> None:
    first = _valid_event(evidence_ids=("ev_b", "ev_a"))
    second = _valid_event(evidence_ids=("ev_a", "ev_b"))

    assert first.deterministic_id() == second.deterministic_id()
'@

Write-TextFile -Path (Join-Path $RootPath "tests\test_deterministic_ids.py") -Content @'
from __future__ import annotations

from decimal import Decimal

import pytest

from smart_money.core.ids import deterministic_id


def test_same_payload_produces_same_id() -> None:
    payload = {"symbol": "SOLUSDT", "price": Decimal("100.0")}
    assert deterministic_id("candle", payload) == deterministic_id("candle", payload)


def test_different_payload_produces_different_id() -> None:
    first = deterministic_id("candle", {"symbol": "SOLUSDT"})
    second = deterministic_id("candle", {"symbol": "BTCUSDT"})

    assert first != second


def test_key_order_does_not_affect_id() -> None:
    first = deterministic_id("candle", {"a": 1, "b": 2})
    second = deterministic_id("candle", {"b": 2, "a": 1})

    assert first == second


def test_namespace_affects_id() -> None:
    payload = {"a": 1}

    assert deterministic_id("candle", payload) != deterministic_id("structure_event", payload)


def test_float_values_are_rejected() -> None:
    with pytest.raises(TypeError, match="float"):
        deterministic_id("candle", {"price": 1.23})
'@

Write-TextFile -Path (Join-Path $RootPath "tests\test_canonical_serialization.py") -Content @'
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from smart_money.core.serialization import canonical_json


def test_dict_key_order_is_stable() -> None:
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_decimal_serializes_as_string() -> None:
    assert canonical_json({"price": Decimal("100.00")}) == '{"price":"100"}'


def test_datetime_serializes_as_canonical_utc_string() -> None:
    value = datetime(2024, 1, 1, 3, 30, tzinfo=timezone(timedelta(hours=3, minutes=30)))

    assert canonical_json({"time": value}) == '{"time":"2024-01-01T00:00:00Z"}'


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        canonical_json({"time": datetime(2024, 1, 1, 0, 0)})


def test_nested_structures_serialize_stably() -> None:
    first = {
        "z": (Decimal("2.0"), {"b": Decimal("3.00"), "a": "x"}),
        "a": [1, None, True],
    }
    second = {
        "a": [1, None, True],
        "z": (Decimal("2.00"), {"a": "x", "b": Decimal("3.0")}),
    }

    assert canonical_json(first) == canonical_json(second)
    assert canonical_json(first) == '{"a":[1,null,true],"z":["2",{"a":"x","b":"3"}]}'
'@

Write-Step "Writing docs"

Write-TextFile -Path (Join-Path $RootPath "docs\slice_0_6_domain_contracts.md") -Content @'
# Slice 0.6 - Domain Contracts, Canonical Serialization, Deterministic IDs

## Scope

This slice introduces the first production-grade immutable domain contracts and deterministic identity utilities.

Implemented contracts:

- `Candle`
- `StructureEvent`

Implemented utilities:

- UTC datetime validation and canonical formatting
- canonical JSON serialization
- deterministic ID generation

## Non-goals

This slice does not implement:

- BOS detection
- CHOCH detection
- liquidity sweep detection
- imbalance detection
- setup detection
- decision logic
- alert logic
- UI
- Persian reporting
- API
- database
- exchange adapters
- broker integration
- trade execution
- ML decisioning

## Contracts Added

### Candle

Immutable OHLCV candle with explicit UTC time semantics and Decimal-only price/volume identity fields.

### StructureEvent

Immutable future market-structure event record. It stores deterministic facts only and does not perform detection.

## Deterministic ID Policy

IDs are generated from:

1. A non-empty namespace.
2. Canonical JSON payload.
3. SHA-256 digest.
4. First 32 hex characters.

Format:
```text
namespace_32hexchars

Examples:

text
candle_7f3a...
structure_event_91ab...

## Canonical Serialization Policy

Canonical JSON uses:

- sorted dictionary keys
- stable compact separators
- ASCII output
- Decimal serialized as normalized string
- datetime serialized as UTC ISO-8601 with `Z`
- tuple/list serialized as arrays
- float rejection for identity serialization

## Validation Rules

Validation is explicit inside `__post_init__`.

Core constructors must not call:

- `datetime.now()`
- `uuid.uuid4()`
- `random`
- `time.time()`
- network clients
- broker clients
- database clients

## Test Coverage Summary

Tests cover:

- valid contract creation
- immutability
- UTC datetime enforcement
- Decimal-only numeric identity
- invalid OHLC rejection
- negative volume rejection
- evidence ID tuple enforcement
- evidence ID canonical sorting
- canonical JSON stability
- deterministic ID stability
- namespace-sensitive IDs
- key-order-independent IDs
- float rejection
'@

Write-Step "Slice 0.6 installation complete"
Write-Host ""
Write-Host "Next commands:" -ForegroundColor White
Write-Host "  `$env:PYTHONPATH = `"src`"" -ForegroundColor Green
Write-Host "  python -m pytest" -ForegroundColor Green


Run it:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install_slice_0_6.ps1
$env:PYTHONPATH = "src"
python -m pytest
