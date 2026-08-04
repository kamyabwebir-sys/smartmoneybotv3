# SmartMoneyBotV3 Slice Governance Skill

Use this skill when implementing, reviewing, or planning SmartMoneyBotV3 slices.

## Project Model

SmartMoneyBotV3 is deterministic, replayable, and slice-based.

Target architecture direction:
- Core
- Domain
- Application
- Adapters
- Analytics
- Reporting

The architecture direction is accepted but must not trigger broad refactors automatically.

## Protected Baseline

Baseline Protected Slice:
- Slice 0.10 — Deterministic Structure Discovery Registry

Protected files:
- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

Do not modify these files unless the user explicitly says the current slice targets them.

## Hard Guardrails

Fail closed if a proposed change adds:
- execution/trading logic
- risk calculation
- opaque ML decisioning
- reporting/UI leakage into core/domain logic

Analytics may only produce evidence and score breakdowns. It must not make direct trading decisions.

## Default Workflow

Before any implementation or review:
1. Identify Active Slice.
2. State target files.
3. State protected files.
4. State expected artifacts.
5. State verification commands.
6. State out-of-scope items.

Implementation must be:
- narrow
- deterministic
- replayable
- testable
- patch-first
- placement-based
- idempotent where installer-based

Avoid broad refactors unless explicitly requested.

## File Scope

Prefer max 3 files per slice unless explicitly authorized.

## Language Rules

- Code, filenames, tests, commit messages: English.
- User-facing explanations/reports: Persian.

## Review Checklist

For each patch, check:
- protected files unchanged
- no execution/trading logic
- no risk calculation
- no opaque ML decisioning
- no reporting leakage into core/domain
- deterministic timestamp/serialization handling
- replayability preserved
- tests/verifiers included where relevant
