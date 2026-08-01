# Slice 1.27 - EM-003 Discovery Registry Read-Only Consumption Contract Lock

Status: READY_FOR_VERIFICATION
Authority Scope: Governance and documentation lock only
Verification Mode: Deterministic, replayable, fail-closed
Evidence Class: Read-only downstream consumption contract

## Purpose

This slice locks the downstream consumption contract for the EM-003 discovery registry.

The registry may be consumed only as deterministic, replayable, read-only evidence metadata. It must not be used as an execution, trading, risk, opaque ML, reporting, or direct decision surface.

## Protected Paths

- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

These paths must remain unchanged by this slice.

## Allowed Consumption

Downstream consumers may read registry outputs only to obtain:

- canonical evidence identity
- evidence case metadata
- deterministic registry references
- replay/audit grounding references

## Prohibited Consumption

Downstream consumers must not use the registry to perform or produce:

- execution logic
- trading logic
- risk calculation
- opaque ML decisioning
- direct setup/decision/trade promotion
- reporting/UI leakage into core/domain logic
- mutation of registry state
- mutation of protected registry behavior

## Acceptance Criteria

- Read-only consumption contract is explicitly locked.
- Protected registry implementation remains unchanged.
- Protected registry tests remain unchanged.
- Verifier is deterministic and fail-closed.
- Verifier emits a canonical governance receipt.
- Receipt includes slice=1.27 and status=PASS.
- No prohibited guardrail terms are introduced as permitted behavior.

## Out of Scope

- No execution/trading logic.
- No risk calculation.
- No opaque ML decisioning.
- No reporting/UI leakage into core/domain logic.
- No edits to src/smart_money/discovery/registry.py.
- No edits to tests/discovery/test_registry.py.
