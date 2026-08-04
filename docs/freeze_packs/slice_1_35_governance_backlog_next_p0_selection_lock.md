# Slice 1.35 — Governance Backlog Next P0 Selection Lock

Status: Installed for verification
Slice: 1.35
Scope: governance-only
Selected backlog tier: P0
Selected item: Governance Artifact and Receipt Inventory Consistency Check

## Current Slice Scope

Slice 1.35 locks the next P0 governance stabilization item for implementation planning:

`Governance Artifact and Receipt Inventory Consistency Check`

This item is selected under the approved Slice 1.31 P0 backlog category:

`Governance Stabilization (Canonical drifts, Fail-closed repairs)`

## Selection Rationale

The selected item is intentionally narrow. It prepares a future governance consistency check for:

- freeze packs
- reviews
- receipts
- verifier expectations
- canonical JSON receipt shape
- protected-file mutation evidence

This slice does not implement the checker. It only locks the next P0 item.

## Guardrails

- No execution or trading logic.
- No risk calculation.
- No opaque ML decisioning.
- No reporting/UI leakage into core/domain logic.
- Analytics does not make direct decisions.
- Protected files remain unchanged:
  - `src/smart_money/discovery/registry.py`
  - `tests/discovery/test_registry.py`

## Out-of-Scope Items

- Runtime pipeline changes.
- Package-root promotion or removal.
- Registry behavior changes.
- Test behavior changes.
- Broker/exchange/wallet automation.
- Functional promotion.
- Implementation of the inventory consistency checker.

## Promotion Gate

Functional promotion remains LOCKED.

## Verification Requirements

The verifier must fail closed unless:

- Slice 1.31 backlog review exists and is Approved.
- Slice 1.31 operating rules exist.
- The Slice 1.35 freeze pack exists and names the selected P0 item.
- The Slice 1.35 review exists and passes.
- The Slice 1.35 receipt is canonical JSON.
- The receipt contains no float values.
- The receipt ID is SHA-256 lowercase hex over canonical JSON without `receipt_id`.
- Protected files are not listed as modified.
