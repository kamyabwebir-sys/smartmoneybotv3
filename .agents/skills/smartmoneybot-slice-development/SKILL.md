# SmartMoneyBot Slice Development

## Purpose

Assist with narrow, deterministic, replayable, slice-based development for SmartMoneyBotV3.

## When to Use

Use this skill when implementing or reviewing a concrete project slice.

## Guardrails

- Do not modify protected files unless explicitly authorized:
  - `src/smart_money/discovery/registry.py`
  - `tests/discovery/test_registry.py`
- No execution or trading logic.
- No risk calculation.
- No opaque ML decisioning.
- No reporting/UI leakage into core/domain logic.
- Keep changes narrow, deterministic, replayable, and testable.
- Prefer max 3 primary files per slice unless the slice explicitly allows more.

## Expected Inputs

- Active Slice number and scope.
- Freeze Pack path, if available.
- Target files.
- Out-of-scope items.
- Verification command, usually:
  - `pytest -q`

## Output Style

Return:

1. Current Slice Scope
2. Proposed Minimal Changes
3. Guardrail Check
4. Verification Plan

## Default Behavior

If a request is ambiguous, propose the safest narrow path instead of broad refactor.
