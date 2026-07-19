# Evidence Matrix: Slice 1.0 - Raw Candle Ingestion Contracts

Status: GOVERNANCE EVIDENCE ONLY
Slice Status: BLOCKED
Implementation Authority: NONE
Approval Status: NOT APPROVED

This document records evidence targets, known gaps, and review requirements for
Slice 1.0. It does not approve implementation, contract shape, package placement,
class names, field names, serialization APIs, validation behavior, deterministic
ID algorithms, fixtures, adapters, or test changes.

Evidence collection alone is insufficient for approval. A separate approval review
must explicitly authorize any implementation after reviewing repository-grounded
evidence.

## Governance Constraints

The following constraints apply to this evidence matrix:

- No source implementation is authorized.
- No test implementation is authorized.
- No package creation or module placement is authorized.
- No raw candle contract shape is authorized.
- No deterministic ID formula is authorized.
- No validation or error behavior is authorized.
- No canonical serialization API is authorized.
- No ingestion runtime behavior is authorized.
- No adapter, exchange, trading, execution, or risk logic is authorized.

## Evidence Sufficiency Levels

Use the following sufficiency levels during review:

- MISSING: no repository-grounded evidence has been cited.
- PARTIAL: some evidence exists, but it does not fully support the claim.
- SUFFICIENT_FOR_REVIEW: evidence is enough to discuss approval, but not approval itself.
- CONFLICTING: cited evidence points to incompatible conclusions.
- OUT_OF_SCOPE: the claim is not required for Slice 1.0 approval.

No row in this matrix grants implementation authority.

## Evidence Matrix

| ID | Claim / Review Need | Required Evidence Source | Current Sufficiency | Known Gap | Approval Impact |
| --- | --- | --- | --- | --- | --- |
| EM-001 | Slice 1.0 must be sequenced after the completed foundation slices. | Build plan, freeze packs, commit history, completed Slice 0.9/0.10/0.11 evidence. | MISSING | Need repository-grounded evidence that foundation contracts are complete and stable enough for Slice 1.0 review. | Blocks approval until sequencing is confirmed. |
| EM-002 | Slice 1.0 scope is limited to raw candle ingestion contracts. | Roadmap, freeze pack text, scope guardrails, prior slice documentation. | PARTIAL | Need explicit evidence that normalization, structure discovery, setup, decision, alerting, execution, and risk are excluded. | Blocks broad implementation. |
| EM-003 | Repository already has deterministic and replayable design constraints. | docs/core_contracts_principles.md:13, docs/deterministic_assumptions_v1.md:10-11, src/smart_money/core/replay.py:7, tests/core/test_golden_replay.py:3,12, docs/freeze_packs/slice_0_10.md:77,143 | SUFFICIENT_FOR_REVIEW | Evidence is available and ready for formal review.| Blocks contract approval if not fully grounded. |
| EM-004 | Existing immutable model conventions should guide any future raw candle contract. | Existing domain model files and tests, immutability tests, dataclass/frozen conventions if present. | MISSING | Need evidence of current immutable contract style before proposing any model shape. | Blocks model-shape approval. |
| EM-005 | Existing canonical serialization conventions must be identified before approving raw candle serialization. | Current serialization utilities, contract tests, golden fixtures, zero-header mode references if present. | MISSING | Need evidence of current canonical ordering, encoding, and stable representation rules. | Blocks serialization approval. |
| EM-006 | Existing deterministic ID conventions must be identified before approving any candle identity. | Prior ID generation code/tests/docs, registry/discovery identifiers, canonical hashing references if present. | MISSING | Need evidence of whether deterministic IDs exist and how they are defined. | Blocks `candle_id` or equivalent approval. |
| EM-007 | Timestamp assumptions must be evidence-grounded. | Existing time handling code/tests/docs, fixture conventions, replay assumptions. | MISSING | Need evidence for allowed timestamp unit, timezone, ordering, and normalization boundaries. | Blocks timestamp contract approval. |
| EM-008 | OHLCV numeric representation must be evidence-grounded. | Existing numeric handling code/tests/docs, serialization conventions, fixture examples. | MISSING | Need evidence for deterministic numeric representation and invalid-value handling. | Blocks OHLCV field approval. |
| EM-009 | Source/provenance representation must be evidence-grounded. | Existing source metadata patterns, adapter boundary docs, ingestion docs if present. | MISSING | Need evidence for how source, venue, symbol, timeframe, and provider metadata are represented or intentionally deferred. | Blocks provenance approval. |
| EM-010 | Error behavior must align with existing domain error contracts. | Slice 0.11 event/error contracts, domain error tests, error manifest if present. | MISSING | Need exact references to current error contract style and allowed error categories. | Blocks validation/error approval. |
| EM-011 | Event behavior must not be introduced unless supported by existing contracts and Slice 1.0 scope. | Slice 0.11 event contracts, freeze pack scope, event tests. | MISSING | Need evidence whether raw candle contract creation emits no events, emits candidate events, or defers events entirely. | Blocks event-related approval. |
| EM-012 | Fixture strategy must follow current deterministic test conventions. | Existing tests, fixture directories, golden file conventions, pytest style. | MISSING | Need evidence for naming, location, canonical examples, and invalid-case style. | Blocks fixture approval. |
| EM-013 | Slice 1.0 must not leak reporting/UI concerns into domain contracts. | Architecture guardrails, reporting docs, current domain/reporting separation. | MISSING | Need evidence of existing separation and explicit exclusion. | Blocks any user-facing/reporting fields. |
| EM-014 | Slice 1.0 must not introduce trading, execution, risk, or ML decisioning. | Scope guardrails, project instructions, existing architecture docs. | PARTIAL | Need repository-grounded citations, not only process memory. | Blocks unsafe expansion. |
| EM-015 | Any future module placement must be approved separately. | Current package structure, freeze pack rules, architecture decision records if present. | MISSING | Need evidence of current valid placement and whether a new module is allowed. | Blocks package/module creation. |
| EM-016 | Slice 1.0 boundary from Slice 1.1 normalization must be explicit. | Roadmap, future slice docs, freeze pack notes. | MISSING | Need evidence that raw ingestion contracts do not include normalization semantics. | Blocks over-scoped contract behavior. |
| EM-017 | Backward compatibility with completed Slice 0.10 registry must be preserved. | `src/smart_money/discovery/registry.py`, `tests/discovery/test_registry.py`, Slice 0.10 freeze pack. | MISSING | Need evidence that Slice 1.0 does not modify or depend on registry internals without approval. | Blocks unrelated discovery changes. |
| EM-018 | Backward compatibility with Slice 0.11 event/error contracts must be preserved. | Slice 0.11 source/tests/docs. | MISSING | Need evidence that any candidate validation/error behavior is compatible with existing contracts. | Blocks error/event changes. |

## Required Repository Evidence Before Approval Review

Before any approval review, collect citations for the following repository evidence:

1. Current git baseline and clean/dirty state.
2. Existing freeze pack for Slice 1.0.
3. Completed Slice 0.9 evidence.
4. Completed Slice 0.10 evidence.
5. Completed Slice 0.11 evidence.
6. Current deterministic/replayable rules.
7. Current immutable model conventions.
8. Current canonical serialization conventions.
9. Current deterministic ID conventions, if any.
10. Current domain error/event conventions.
11. Current pytest style and fixture conventions.
12. Current package/module layout relevant to domain contracts.
13. Explicit scope guardrails excluding execution, risk, ML decisioning, reporting, and UI.

Each evidence item must cite concrete repository files and, where possible, line ranges.

## Known Open Questions

The following questions are review inputs only. They do not approve any decision.

1. Does Slice 1.0 require a raw candle contract at all, or only contract constraints?
2. If a raw candle contract is later approved, where should it live?
3. Which fields are required for raw ingestion versus later normalization?
4. Is identity required at ingestion time, or deferred?
5. If identity is required, is it generated, supplied, or derived?
6. What timestamp representation is compatible with deterministic replay?
7. What numeric representation is compatible with canonical serialization?
8. Which invalid inputs should be rejected at contract creation time?
9. Which invalid inputs should be deferred to normalization?
10. Which failures map to existing domain errors?
11. Are domain events relevant to raw candle ingestion, or out of scope?
12. What golden fixtures are required before implementation?
13. How does Slice 1.0 avoid coupling to adapters, providers, or exchanges?
14. How does Slice 1.0 avoid reporting/UI leakage?
15. What explicitly belongs to Slice 1.1 instead of Slice 1.0?

## Explicit Non-Approval

This evidence matrix does not approve:

- `RawCandle` as a class name.
- `candle_id` as a field.
- any ID algorithm.
- any timestamp unit.
- any timezone rule.
- any OHLCV numeric type.
- any source/provenance field names.
- any validation behavior.
- any error class.
- any event class.
- any serialization method.
- any module path.
- any fixture path.
- any source code changes.
- any test code changes.

## Review Exit Criteria

Slice 1.0 may only move toward approval after a separate review confirms:

1. Required repository evidence has been collected and cited.
2. Conflicting evidence has been resolved or explicitly deferred.
3. Slice boundaries are clear.
4. Out-of-scope items remain excluded.
5. Implementation authority is explicitly granted by a separate approval document or approved Freeze Pack update.

Until then, Slice 1.0 remains BLOCKED.
