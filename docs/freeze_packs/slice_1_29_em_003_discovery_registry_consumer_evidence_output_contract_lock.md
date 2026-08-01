# Slice 1.29 - EM-003 Discovery Registry Consumer Evidence Output Contract Lock

## Governance Status

Status: CLOSED-CANDIDATE
Promotion Gate: LOCKED
Slice Type: Governance-only
Authority: EM-003 evidence governance
Verifier Mode: Fail-closed

## Purpose

This slice locks the expected evidence output contract for future Discovery Registry consumers.

Slice 1.28 locked the consumer interface shape. Slice 1.29 locks the shape and boundary rules of the evidence output that a compliant consumer may emit after reading from the deterministic Discovery Registry.

This slice does not implement a consumer, modify registry code, alter registry tests, or introduce runtime behavior.

## Current Slice Scope

This slice defines a governance contract for consumer evidence output only.

A compliant consumer evidence output may include:

- registry snapshot reference
- registry entry reference
- evidence references
- deterministic score breakdown
- replay manifest reference
- consumer version
- output schema version
- boundary compliance markers

A compliant consumer evidence output must not include:

- trade execution instruction
- order intent
- position sizing
- stop loss or take profit calculation
- risk score used as a decision
- opaque ML decision
- reporting or UI formatted payload
- direct promotion verdict

## Locked Evidence Output Shape

A compliant Discovery Registry consumer evidence output is expected to be shaped around these conceptual fields:

- `schema_version`
- `consumer_version`
- `registry_snapshot_id`
- `registry_entry_id`
- `evidence_refs`
- `deterministic_score_breakdown`
- `replay_manifest_ref`
- `boundary_status`
- `generated_from`

The interface remains governance-level only in this slice. No Python classes, protocols, runtime adapters, registry consumers, or analytics implementation are created.

## Required Output Constraints

A compliant evidence output must satisfy these constraints:

- Evidence-only: output may describe evidence and score breakdown, not decisions.
- Deterministic: identical registry input and consumer version yield identical evidence output.
- Replayable: output must retain stable references to registry input and replay manifest identity.
- Read-only: output generation must not mutate registry content.
- Boundary-safe: output must not leak execution, risk, opaque ML decisioning, reporting, or UI behavior into core/domain logic.
- Auditable: output must contain enough stable references for later verifier inspection.
- Narrow: output must remain limited to registry-consumer evidence semantics.

## Boundary Status Contract

The conceptual `boundary_status` field is locked as a governance marker for future implementation slices.

It may represent these conceptual states:

- `BOUNDARY_SAFE`
- `BOUNDARY_BLOCKED`
- `EVIDENCE_INCOMPLETE`
- `REPLAY_REFERENCE_MISSING`

These are not runtime enum values in this slice. They are governance vocabulary for future verification.

## Protected Paths

The following paths are protected and must remain unchanged by this slice:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

## Out-of-Scope Items

This slice does not:

- implement a Discovery Registry consumer
- implement analytics scoring
- modify the discovery registry
- modify registry tests
- add execution or trading logic
- add risk calculation
- add opaque ML decisioning
- add reporting or UI behavior
- alter canonical serialization
- alter replay manifest behavior
- promote EM-003 beyond the locked governance state

## Acceptance Criteria

The slice is accepted only if:

- freeze pack exists
- review document exists
- verifier exists
- canonical governance receipt is emitted
- protected paths remain unchanged
- required governance tokens are present
- forbidden behavior tokens are explicitly blocked by the contract
- verifier fails closed when required files, tokens, or protected path hashes do not match

## Final Status

This slice may be marked CLOSED / PASS only after the verifier emits a canonical governance receipt with status PASS.
