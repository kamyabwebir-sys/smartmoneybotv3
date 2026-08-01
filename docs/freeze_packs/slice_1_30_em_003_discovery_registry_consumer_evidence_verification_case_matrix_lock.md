# Slice 1.30 - EM-003 Discovery Registry Consumer Evidence Verification Case Matrix Lock

## Governance Status

Status: CLOSED-CANDIDATE
Promotion Gate: LOCKED
Slice Type: Governance-only
Authority: EM-003 evidence governance
Verifier Mode: Fail-closed

## Purpose

This slice locks the verification case matrix for future Discovery Registry consumer evidence outputs.

Slice 1.28 locked the consumer interface shape.
Slice 1.29 locked the consumer evidence output contract.
Slice 1.30 locks the verifier case matrix that future implementation slices must satisfy before any concrete consumer evidence output may be accepted.

This slice does not implement a consumer, analytics scoring, registry reading behavior, runtime validation, or reporting behavior.

## Current Slice Scope

This slice defines governance-level verifier cases for the evidence output contract only.

It locks expected PASS and FAIL cases for future verifier implementation.

## Locked Verification Case Matrix

A future verifier for Discovery Registry consumer evidence output must cover these required cases:

| Case ID | Case Name | Expected Result | Locked Rule |
|---|---|---:|---|
| EM003-CONS-EV-001 | complete evidence output shape | PASS | Required conceptual fields are present. |
| EM003-CONS-EV-002 | deterministic replay identity retained | PASS | Registry snapshot, entry reference, replay manifest reference, schema version, and consumer version are stable. |
| EM003-CONS-EV-003 | evidence references retained | PASS | Evidence refs are present and auditable. |
| EM003-CONS-EV-004 | deterministic score breakdown only | PASS | Score breakdown is explanatory evidence, not a decision. |
| EM003-CONS-EV-005 | read-only registry consumption | PASS | Output generation does not mutate registry content. |
| EM003-CONS-EV-006 | missing registry snapshot reference | FAIL | Output cannot be replay-audited without registry snapshot identity. |
| EM003-CONS-EV-007 | missing registry entry reference | FAIL | Output cannot be traced to a registry entry. |
| EM003-CONS-EV-008 | missing replay manifest reference | FAIL | Output cannot satisfy replay traceability. |
| EM003-CONS-EV-009 | execution instruction present | FAIL | Execution behavior is forbidden. |
| EM003-CONS-EV-010 | order intent present | FAIL | Trading intent is forbidden. |
| EM003-CONS-EV-011 | position sizing present | FAIL | Risk/execution sizing is forbidden. |
| EM003-CONS-EV-012 | stop loss or take profit calculation present | FAIL | Risk calculation is forbidden. |
| EM003-CONS-EV-013 | opaque ML decision present | FAIL | Opaque decisioning is forbidden. |
| EM003-CONS-EV-014 | reporting/UI formatted payload present | FAIL | Reporting/UI leakage is forbidden. |
| EM003-CONS-EV-015 | direct promotion verdict present | FAIL | Evidence output may not directly promote governance state. |

## Required Future Verifier Behavior

A future concrete verifier must fail closed when:

- any required evidence output field is missing
- registry snapshot identity is missing
- registry entry identity is missing
- replay manifest reference is missing
- evidence refs are missing
- score breakdown is used as a decision
- output contains execution instruction
- output contains order intent
- output contains position sizing
- output contains risk calculation
- output contains opaque ML decisioning
- output contains reporting or UI formatting
- output contains direct promotion verdict
- protected registry paths are mutated by the implementation slice

## Required Positive Assertions

A future concrete verifier must assert:

- output is evidence-only
- output is deterministic
- output is replayable
- output is read-only
- output is auditable
- output includes deterministic score breakdown
- output preserves registry traceability
- output preserves replay manifest traceability
- output remains inside analytics evidence boundaries

## Required Negative Assertions

A future concrete verifier must reject:

- execution/trading logic
- risk calculation
- order intent
- position sizing
- stop loss or take profit calculation
- opaque ML decisioning
- reporting/UI leakage
- direct governance promotion verdicts emitted by analytics output

## Protected Paths

The following paths are protected and must remain unchanged by this slice:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

## Out-of-Scope Items

This slice does not:

- implement a Discovery Registry consumer
- implement runtime validation
- implement analytics scoring
- implement score calculation
- modify the discovery registry
- modify registry tests
- add execution or trading logic
- add risk calculation
- add opaque ML decisioning
- add reporting or UI behavior
- alter replay manifest behavior
- alter canonical serialization
- promote EM-003 beyond the locked governance state

## Acceptance Criteria

The slice is accepted only if:

- freeze pack exists
- review document exists
- verifier exists
- canonical governance receipt is emitted
- protected paths remain unchanged
- required PASS cases are present
- required FAIL cases are present
- required positive assertions are present
- required negative assertions are present
- verifier fails closed when required files, tokens, or protected path hashes do not match

## Final Status

This slice may be marked CLOSED / PASS only after the verifier emits a canonical governance receipt with status PASS.
