# Slice 1.34 — Discovery Consumer Compatibility Debt Closure

## Status

LOCKED_FOR_REVIEW

## Purpose

Close the governance debt introduced by the Slice 1.32 / Slice 1.33 compatibility repair around
`ConsumerEvidenceProjection`.

This slice records the final accepted contract split:

- `to_dict()` preserves the Slice 1.32 locked deterministic evidence shape.
- `to_canonical_dict()` exposes the Slice 1.33 verifier-facing canonical shape.
- `generated_from` is retained as deterministic provenance metadata and is only emitted through
  `to_canonical_dict()`.

## Scope

In scope:

1. Document the compatibility closure between Slice 1.32 and Slice 1.33.
2. Record the regression-safe serialization split.
3. Capture the verification evidence:
   - `tests/discovery/test_consumer.py` passed.
   - `tests/governance/test_consumer_verifier.py` passed.
   - combined consumer/verifier test run passed.
4. Confirm protected files remained unchanged:
   - `src/smart_money/discovery/registry.py`
   - `tests/discovery/test_registry.py`

## Non-Scope

This slice does not introduce:

- execution logic
- trading logic
- risk calculation
- opaque ML decisioning
- reporting/UI payloads
- registry mutation
- promotion verdict authority
- broad architecture refactor

## Contract Closure

The accepted serialization contract is:
```text
ConsumerEvidenceProjection.to_dict()
-> legacy locked Slice 1.32 evidence projection shape
-> excludes generated_from

ConsumerEvidenceProjection.to_canonical_dict()
-> governance verifier-facing Slice 1.33 canonical shape
-> includes generated_from

## Determinism and Replayability

The closure is deterministic because:

- the projection remains immutable/frozen;
- nested mappings are frozen with deterministic key ordering;
- canonical verifier output is derived from the locked legacy output plus explicit provenance;
- no runtime clock, random value, network call, execution path, or risk calculation is introduced.

## Verification Evidence

Observed local verification:

text
python -m pytest tests/discovery/test_consumer.py tests/governance/test_consumer_verifier.py -q
..... [100%]
5 passed

python -m pytest tests/discovery/test_consumer.py -q
... [100%]
3 passed

python -m pytest tests/governance/test_consumer_verifier.py -q
.. [100%]
2 passed

The pytest-asyncio deprecation warning is non-blocking and outside the scope of this slice.

## Protected File Statement

The following protected files are not part of this closure and must remain unchanged:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

## Closure Verdict

READY_FOR_CLOSURE_REVIEW
