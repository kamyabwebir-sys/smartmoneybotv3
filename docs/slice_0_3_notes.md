# Slice 0.3 Notes

Status: Installed

## Goal

Freeze semantic meaning of core domain vocabulary before implementing contracts and logic.

## Files Added

- docs/core_contract_semantics_v1.md
- docs/reason_codes_seed_v1.md
- docs/evidence_policy_v1.md
- docs/deterministic_assumptions_v1.md
- tests/test_semantic_docs_exist.py
- tests/test_semantic_keywords.py

## Acceptance Criteria

- Semantic documents exist.
- Mandatory terms are present.
- Deterministic assumptions are explicitly documented.
- AI boundary is explicitly documented.
- Reason code naming seed exists.

## Out Of Scope

- Python models
- Validation code
- Serialization code
- Event ids
- Structure engine
- Setup engine
- Reporting implementation

## Patch Notes

Prerequisite: Slice 0.2 must already be installed and passing.

These tests are governance smoke tests. They verify required documents and terms exist; they do not prove semantic correctness.
