# Slice 1.28 - EM-003 Discovery Registry Consumer Interface Shape Lock

## Governance Status

Status: CLOSED-CANDIDATE
Promotion Gate: LOCKED
Slice Type: Governance-only
Authority: EM-003 evidence governance
Verifier Mode: Fail-closed

## Purpose

This slice locks the expected shape of any Discovery Registry consumer interface without implementing the consumer, modifying the registry, or introducing execution, risk, reporting, UI, or opaque ML decisioning behavior.

Slice 1.27 locked read-only consumption semantics. Slice 1.28 locks the interface shape that downstream consumers must respect when reading from the deterministic discovery registry.

## Current Slice Scope

This slice defines a governance contract for registry consumers:

- Consumers may read deterministic registry entries.
- Consumers must not mutate registry contents.
- Consumers must not derive trading execution decisions from registry data.
- Consumers must not calculate risk from registry data.
- Consumers must not introduce opaque ML decisioning.
- Consumers must preserve replayability by treating registry input as stable evidence.
- Consumers must expose evidence and score breakdown only when operating inside analytics boundaries.
- Consumers must keep reporting and UI concerns outside core/domain logic.

## Locked Consumer Interface Shape

A compliant Discovery Registry consumer interface is expected to be shaped around these conceptual fields:

- `registry_snapshot_id`
- `registry_entry_id`
- `structure_type`
- `source_timeframe`
- `evidence_refs`
- `deterministic_score_breakdown`
- `replay_manifest_ref`
- `consumer_version`

The interface shape is governance-level only in this slice. It does not create Python interfaces, classes, protocols, adapters, or runtime code.

## Required Interface Constraints

A compliant consumer must satisfy these constraints:

- Read-only: no registry mutation.
- Deterministic: identical registry input yields identical consumer evidence output.
- Replayable: output can be traced back to stable evidence references and replay manifest references.
- Evidence-first: the consumer may expose evidence and score breakdown, not direct decisions.
- Boundary-safe: no execution, risk, reporting, UI, or opaque ML decisioning leaks into core/domain behavior.
- Narrow: consumer behavior must remain limited to registry consumption semantics.

## Protected Paths

The following paths are protected and must remain unchanged by this slice:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

## Out-of-Scope Items

This slice does not:

- implement a registry consumer
- modify the discovery registry
- modify registry tests
- add execution or trading logic
- add risk calculation
- add ML decisioning
- add reporting/UI behavior
- promote EM-003 beyond the locked governance state

## Acceptance Criteria

The slice is accepted only if:

- freeze pack exists
- review document exists
- verifier exists
- canonical governance receipt is emitted
- protected paths remain unchanged
- required governance tokens are present
- verifier fails closed when required files or tokens are missing

## Final Status

This slice may be marked CLOSED / PASS only after the verifier emits a canonical governance receipt with status PASS.
