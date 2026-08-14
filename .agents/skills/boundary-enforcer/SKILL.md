---
name: boundary-enforcer
description: Enforce deterministic, side-effect-free architecture boundaries in smartmoneybotv3. Use when changing Core, Domain, Analytics, Application, Replay, scoring, traceability, providers, persistence wiring, or dependencies; when reviewing a Slice before commit; or when checking that network and filesystem concerns remain outside pure layers.
---

# Boundary Enforcer

Keep replay and analytical code deterministic by rejecting forbidden imports,
filesystem access in pure layers, and dependency-direction violations.

## Workflow

1. Run the contract verifier before changing Python:

   ```powershell
   pwsh -NoProfile -File .\verify_contract_integrity.ps1
   ```

2. Inspect `git status --short` and preserve unrelated changes.
3. Run the boundary checker before the patch:

   ```powershell
   python .agents/skills/boundary-enforcer/scripts/check_boundaries.py
   ```

4. Keep changes slice-based and within the authorized file budget.
5. Run targeted tests, the boundary checker, Ruff, and the full test suite.
6. Fail closed on any violation. Do not suppress, dynamically import, alias, or
   relocate a forbidden dependency merely to evade the checker.
7. Report verifier status, boundary status, tests, protected-file status, and
   the exact changed files as the Slice receipt.

## Boundaries

- `core/`, `domain/`, and `analytics/` must not read files, write files, open
  sockets, call HTTP/RPC clients, or import persistence/reporting adapters.
- `application/` may orchestrate existing Ledger and Adapter interfaces but
  must not call network clients directly.
- Network and chain SDKs belong in `adapters/`.
- Filesystem persistence belongs in `adapters/persistence/`.
- Human-readable output belongs in `reporting/`.
- Analytics may calculate deterministic evidence and score breakdowns, but it
  must not execute trades, calculate risk, or make opaque ML decisions.
- Preserve canonical serialization, immutable contracts, stable IDs, and
  Replay linkage.
- Do not change protected Discovery files unless explicitly placed in scope.
- Any future Evidence schema version change requires an explicit dual-read
  migration Slice for legacy Ledger data.

## Checker

Run:

```powershell
python .agents/skills/boundary-enforcer/scripts/check_boundaries.py
```

The checker parses Python with `ast`, reports sorted `path:line` violations,
and returns a non-zero exit code on failure. Treat parser failures as boundary
failures.

Review semantic side effects that static imports cannot prove, including:

- injected callables that perform network or disk I/O;
- hidden subprocess or dynamic-import usage;
- mutable global caches affecting Replay;
- wall-clock, randomness, or environment-dependent scoring;
- direct Trading Execution or Risk Calculation.
