# Testing Strategy

Status: Frozen for Foundation Phase

## Testing Goals

Tests must prove:
- Determinism.
- Replayability.
- Contract invariants.
- Stable serialization.
- Cross-platform behavior.
- Clear reporting from evidence.
- No accidental network dependency in core tests.

## Test Layers

### Unit Tests

Purpose:
- Validate small functions and contracts.

Required for:
- Contract invariants.
- Timestamp validation.
- Decimal validation.
- Ordering logic.
- ID generation.
- Risk flag creation.

### Golden/Snapshot Tests

Purpose:
- Ensure canonical output does not change accidentally.

Required for:
- Contract serialization.
- Event lists.
- Setup candidates.
- Discovery candidates.
- Report views.

Rules:
- Snapshots must be deterministic.
- Snapshot changes require review.
- Snapshot changes require explanation.

### Replay Tests

Purpose:
- Ensure same input produces same output.

Replay test must verify:
- Same fixtures.
- Same rules.
- Same output IDs.
- Same ordering.
- Same reports.

### Fixture-Driven Scenario Tests

Purpose:
- Represent domain scenarios.

Examples:
- Simple candle sequence.
- BOS-like sequence after semantic definition.
- Sweep-like sequence after semantic definition.
- Token launch scenario.
- Wallet cluster scenario.
- Pump/dump-like anomaly scenario.

### Contract Validation Tests

Purpose:
- Ensure invalid objects fail early.

Examples:
- Naive datetime rejected.
- Negative volume rejected when not allowed.
- Empty symbol rejected.
- Invalid schema version rejected.
- Mutable defaults not used.

### Cross-Platform Smoke Tests

Purpose:
- Ensure Windows and Linux compatibility.

Check:
- Path handling.
- Newline handling.
- UTF-8 handling.
- PowerShell scripts.
- Python test invocation.

## Network Policy

Unit/domain/core tests:
- No network.
- No RPC.
- No live API.
- No Telegram call.
- No AI call.

Adapter tests:
- Use fixtures/mocks by default.
- Live integration tests must be explicitly marked.
- Live tests must be skipped by default.

## AI Test Policy

AI implementation is deferred.

When AI is introduced:
- Mock model outputs in tests.
- Store prompt template version.
- Store model/provider metadata.
- Verify AI cannot modify deterministic facts.
- Verify AI output references evidence.

## Reporting Test Policy

Reports should be tested through:
- Structured report models.
- Persian text snapshots for important templates.
- Evidence references.
- Error explanation scenarios.

Reports must disclose:
- What was executed.
- What data was used.
- What failed.
- What was skipped.
- Why candidates matter.
- What is unknown.
- Risk evidence.

## Pump/Dump Testing Policy

Tests must avoid overclaiming.

Expected outputs should use:
- suspicious.
- coordinated-looking.
- anomaly.
- evidence-backed.

Tests should not expect:
- confirmed manipulation.
- legal attribution.
- guaranteed prediction.

## Acceptance Rule

A feature is not complete unless it has:
- Invariant tests.
- Serialization tests if contract is serializable.
- Replay or fixture test if deterministic.
- Documentation update if semantics changed.
