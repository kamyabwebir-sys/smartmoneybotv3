# Slice 1.22 - EM-003 Canonical Closure Receipt Lock

**Status:** PROPOSED  
**Scope Mode:** governance-only  
**EM-003 Status:** PARTIAL  
**Promotion Gate:** LOCKED  
**Authority Granted:** NONE  

## Objective

Lock a canonical governance closure receipt shape for deterministic and replayable governance review.

## Canonical Receipt Shape
```json
{
  "schema_version": "1",
  "receipt_type": "em_003_canonical_closure_receipt",
  "slice_id": "1.22",
  "governed_slice_id": "1.21",
  "governance_verdict": "PASS",
  "scope_mode": "governance-only",
  "em_003_status_after_closure": "PARTIAL",
  "promotion_gate_after_closure": "LOCKED",
  "authority_grant": {
"implementation": false,
"promotion": false
  }
}

## Determinism Requirements

- UTF-8 encoding
- No BOM
- Stable key ordering
- No wall-clock timestamp
- No random input
- No PID
- No filesystem enumeration dependency
- No environment-variable dependency
- No manual receipt ID injection

## Fail-Closed Rules

Fail if any of the following occurs:

1. Missing required field
2. Unknown field used for authority expansion
3. `implementation` is `true`
4. `promotion` is `true`
5. EM-003 status changes from `PARTIAL`
6. Promotion Gate changes from `LOCKED`
7. Receipt shape includes runtime, trading, risk, ML, reporting, UI, or adapter behavior

## Out of Scope

- Runtime implementation
- Trading logic
- Risk logic
- ML decisioning
- Promotion of EM-003
- Unlocking Promotion Gate
- Changes to `src/`
- Changes to `tests/`
## Explicit Non-Code Scope Lock

- Changes to `src/` are explicitly out of scope for Slice 1.22.
- Changes to `tests/` are explicitly out of scope for Slice 1.22.
