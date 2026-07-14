# Core Contracts Principles

Status: Frozen for Foundation Phase

## Purpose

Contracts define stable data boundaries between platform components.

They must be:
- Deterministic.
- Explicit.
- Immutable.
- Versioned.
- Serializable.
- Testable.
- Explainable.

## Python Model Policy

Use:
- Python 3.11 or newer.
- dataclasses for early immutable contracts.

Recommended pattern:
```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

@dataclass(frozen=True, slots=True)
class ExampleContract:
schema_version: str
event_id: str
occurred_at: datetime
value: Decimal

Rules:
- Use `@dataclass(frozen=True, slots=True)`.
- Do not use mutable default values.
- Use explicit optional fields.
- Use enums where semantics matter.
- Validate invariants in constructors or factory functions.
- Keep contracts small and composable.

## Schema Version Policy

Every serializable contract must include:
- schema_version.

Breaking changes require:
- Version bump.
- Fixture update.
- Snapshot update.
- Migration note.
- Documentation update.

## ID Policy

IDs must be deterministic when used for replayable events.

Potential deterministic ID inputs:
- schema version.
- symbol/market.
- timeframe.
- event type.
- event timestamp.
- event sequence.
- canonical payload hash.

Do not use random UUIDs for deterministic domain events.

Random IDs are only allowed for external operational records where replay stability is not required.

## Numeric Policy

Use Decimal for:
- price.
- volume.
- liquidity.
- size.
- amount.
- ratio where exactness matters.
- token supply-like values when precision matters.

Use int for:
- counts.
- indexes.
- block heights.
- sequence numbers.

Avoid float in canonical contracts.

If float is unavoidable:
- Document why.
- Keep it outside canonical replay contracts if possible.
- Test serialization stability.

## Time Policy

Use timezone-aware UTC datetimes only.

Rules:
- No naive datetime.
- No local timezone in contracts.
- No wall-clock calls inside deterministic core.
- Input timestamps must be explicit.

Candle policy:
- Candles are identified by open_time.
- Candles passed to core are considered closed/complete.
- Incomplete/live candles belong outside deterministic core.

## Ordering Policy

Candles:
- Order by market, symbol, timeframe, open_time.

Events:
- Order by market, symbol, timeframe, event_time, event_type, sequence.

Wallet relations:
- Normalize node IDs.
- Order by source_node_id, target_node_id, relation_type.

Discovery candidates:
- Order by stable scoring tuple.
- Never rely on accidental insertion order.

## Serialization Policy

Canonical JSON must be stable.

Rules:
- Stable field order.
- Stable Decimal representation.
- Stable datetime representation.
- Stable enum representation.
- No non-deterministic dictionary ordering.
- No hidden fields.

Recommended datetime format:
- ISO 8601 UTC.
- Use `Z` or explicit `+00:00` consistently.

Recommended Decimal format:
- String representation.
- No binary float conversion.

## Evidence Policy

Every important conclusion should reference evidence.

Examples:
- A setup candidate references structure events and context events.
- A risk flag references source data and rule version.
- A wallet cluster references wallet relations.
- A pump/dump-like anomaly references market and wallet evidence.

Evidence should include:
- evidence_id.
- evidence_type.
- source_contract_id.
- rule_version.
- short explanation.
- confidence or severity when applicable.

## Risk Flag Policy

Risk flags must be:
- Named.
- Versioned.
- Evidence-backed.
- Explainable.
- Separated from AI narration.

Risk flags should not be hidden inside natural-language reports.

## Contract Boundary Policy

Do not mix these concepts too early:
- StructureEvent.
- ContextEvent.
- DecisionEvent.
- AlertCandidate.
- SetupCandidate.
- ReportView.

Avoid creating decision events before deterministic setup semantics are stable.

Avoid creating alert candidates before reporting and delivery boundaries are stable.

## Domain Terms Requiring Spec Before Implementation

Do not implement these until defined:
- BOS.
- CHOCH.
- sweep.
- FVG.
- liquidity zone.
- imbalance.
- smart wallet.
- suspicious cluster.
- pump/dump-like anomaly.
- token discovery candidate.
- source reliability.
