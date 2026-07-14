# Core Contract Shape v1

Status: Proposed Freeze for Slice 0.4

This document is documentation-only.

Core constructors must never read wall-clock time implicitly.
created_at must be supplied explicitly by pipeline or replay context.

Required identity fields:
- schema_version
- contract_type
- id

The contract shape defines deterministic ID inputs and canonical serialization.

## Candle


```python
Candle(schema_version, contract_type, id, market, symbol, timeframe, created_at)

```

## StructureEvent


```python
StructureEvent(schema_version, contract_type, id, event_type, occurred_at, created_at)

```

## EvidenceItem


```python
EvidenceItem(schema_version, contract_type, id, evidence_type, created_at)

```

## Unresolved Freeze Gates Before Python Models

- exact schema_version format
- exact contract_type registry
- UTC timestamp text format and precision
- Decimal JSON representation and normalization
- canonical key ordering
- fields participating in deterministic ID inputs
- collection ordering and duplicate policy
- evidence payload shape
- created_at identity and serialization participation