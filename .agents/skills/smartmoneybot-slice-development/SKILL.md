# SmartMoneyBot Slice Development Skill

## Purpose

Help implement and review narrow, deterministic, replayable SmartMoneyBotV3 slices with minimal repo impact.

## Guardrails

Do not introduce:

- execution or trading logic
- broker/exchange automation
- wallet signing
- risk calculation
- position sizing
- leverage logic
- live trading decisions
- opaque ML decisioning
- reporting/UI leakage into core or domain logic

Analytics may produce evidence and score breakdowns, but must not make direct trading decisions.

## Protected Files

Do not modify these files unless explicitly authorized for the current slice:

- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

## Default Behavior

Prefer the smallest safe path.

Use:

- patch-first changes
- placement-based edits
- idempotent installers when useful
- narrow scope
- deterministic and replayable behavior
- no broad refactor without explicit request

## Standard Output

When useful, respond with:

1. Current Slice Scope
2. Minimal Proposed Changes
3. Guardrail Check
4. Verification Plan

## Verification

Before commit, recommend:

git status --short
git diff --check
pytest -q
