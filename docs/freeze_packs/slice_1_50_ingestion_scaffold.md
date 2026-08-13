# Slice 1.50 — Evidence Ingestion Pipeline Scaffold

## Status

- Scope: deterministic in-memory ingestion scaffold
- Implementation authority: limited to ingestion contracts, provider, and tests
- Execution, trading, risk, ML decisioning, and reporting authority: none
- Protected baseline: Slice 0.10

## Objective

Provide a deterministic, replayable, fail-closed boundary for accepting
already-supplied evidence. This slice does not fetch live market data and does
not produce signals, decisions, alerts, orders, or risk outputs.

## Canonical implementation

- `src/smart_money/ingestion/provider.py`
- `tests/ingestion/test_provider_scaffold.py`
- `scripts/verify_slice_1_50_ingestion_scaffold.ps1`

## Required behavior

- Identical canonical input produces the same identifier and result.
- Duplicate input is idempotent.
- Unknown, malformed, or forbidden payloads fail closed.
- Validation occurs through an explicit contract gate.
- No wall-clock, random, network, or environment-dependent behavior is used.
- No reporting/UI concern enters Core, Domain, or Discovery.

## Protected files

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

## Verification

The verifier checks the implementation surface, forbidden I/O dependencies,
required deterministic tests, and protected-file stability.
