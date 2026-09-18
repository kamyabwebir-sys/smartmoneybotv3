# Dashboard R8 Verification and Production Gate Policy

## Scope

This policy governs dashboard runtime, query, audit, recovery, and dashboard
persistence code selected by `scripts/dashboard_release_gate.py`.

The gate is evidence-first, deterministic in file selection, read-only with
respect to dashboard domain state, and fail-closed.

## R8.7 Verification Evidence

R8.7 is satisfied only when the gate:

1. discovers at least one dashboard source file and one dashboard test file;
2. executes every matched dashboard test through `python -m pytest`;
3. obtains pytest exit code `0`;
4. obtains valid JUnit XML with at least one executed test;
5. observes zero failures, zero errors, and zero skipped tests; and
6. writes a manifest and unsigned verification receipt under
   `artifacts/dashboard/r8/`.

An R8.7 receipt has `production_authority: not_granted`. It is evidence only
and must not be interpreted as production authorization.

## R8.8 Production Gate

R8.8 is satisfied only when all R8.7 conditions hold and the invocation also:

1. starts from a clean Git worktree;
2. records the checked-out commit in its manifest and receipt;
3. runs in the protected GitHub Environment `dashboard-production`; and
4. creates a detached RSA-SHA256 signature for the receipt.

The private key is supplied through the GitHub Environment secret
`DASHBOARD_GATE_PRIVATE_KEY_PEM_B64`. It is decoded into `RUNNER_TEMP`,
never committed, and removed after use.

## Evidence Retention

Generated manifests, JUnit XML, pytest output, receipts, and detached
signatures are ignored by Git. GitHub Actions uploads them as workflow
artifacts. A stale successful receipt is deleted before every verification
attempt. Failed verification creates `verification-failure.json` and exits
non-zero without issuing a successful receipt.

## Authority Boundary

This gate verifies evidence. It does not alter dashboard domain state, promote
a release by itself, or replace any independent organizational approval
required for deployment.