# Slice 0.9 Freeze Pack: Deterministic Config Contracts

## Slice Identity

- Slice: 0.9
- Title: Deterministic Config Contracts
- Implementation commit: 2dfe777 `slice/0.9: add deterministic config contracts`
- Freeze pack type: retrospective documentation backfill

## Purpose

Slice 0.9 defines deterministic configuration contracts in the core layer. The goal is to provide stable, validated, and testable configuration primitives without introducing runtime side effects, external dependencies, persistence, or architectural boundary changes.

## Scope

This slice adds deterministic config contract behavior under the existing `smart_money.core` namespace.

Included files:

- `src/smart_money/core/config.py`
- `tests/core/test_config_contracts.py`

## Contract Expectations

The config contracts are expected to be:

- deterministic across repeated construction and serialization paths
- explicit about required and optional fields
- validated at object boundaries
- independent from environment variables, file I/O, network I/O, clocks, randomness, or process-global state
- compatible with the existing core-layer architecture

## Behavioral Requirements

The implementation must preserve the following behavior:

- valid configuration inputs construct successfully
- invalid configuration inputs fail predictably
- default values, if present, are deterministic and documented by tests
- nested or composed config values retain deterministic behavior
- exported or comparable representations remain stable across calls
- validation errors are covered by unit tests

## Out Of Scope

This slice does not introduce:

- application runtime wiring
- environment variable loading
- YAML, TOML, JSON, or `.env` file parsing
- CLI configuration handling
- persistence
- network access
- database-backed settings
- dependency injection containers
- package renames or module relocation
- changes to the o3 architectural boundary model

## Tests

Primary test coverage:

- `tests/core/test_config_contracts.py`

Expected validation commands:
```powershell
pytest tests/core/test_config_contracts.py
pytest
git diff --check
git status --short

## Acceptance Criteria

Slice 0.9 is accepted when:

- deterministic config contracts exist in `src/smart_money/core/config.py`
- unit tests cover valid construction, invalid inputs, defaults, and deterministic behavior
- targeted tests pass
- the full test suite passes
- `git diff --check` reports no whitespace issues
- Git working tree is clean after commit

## Commit Reference

Implementation commit:

text
2dfe777 slice/0.9: add deterministic config contracts

Suggested freeze pack commit message:

text
Docs: add Slice 0.9 freeze pack
