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
