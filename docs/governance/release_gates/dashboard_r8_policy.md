# Dashboard R8 Verification and Signed Gate Policy

Status: Proposed implementation contract; requires repository-owner approval.
Schema: smartmoney.dashboard.r8.v1
Scope: dashboard-revision-verification

## R8.7

- Runtime adapters and the specified runtime tests must exist and be tracked.
- The reviewed baseline must be committed and the tracked tree must be clean.
- Unexpected untracked files are rejected.
- Generated evidence under artifacts/dashboard/evidence/ must not be tracked.
- Every discovered tests/**/test_dashboard_*.py is run explicitly.
- The complete tests/ suite is then run.
- Both runs require exit code zero, nonzero tests, and zero errors,
  failures, or skipped tests.
- Standard pytest JUnit XML is the source for structured test counts.
- Test commands, logs, package inventory, environment, and hashes are recorded.
- All tracked regular files are hashed before and after execution.
- Symlinks and submodule entries are not supported by this version.
- Source changes during verification reject the run.
- No pytest JSON plugin is required.

## R8.8

- Verification evidence must pass and belong to the same CI run and revision.
- Source, manifest, JUnit XML, logs, and package inventory are revalidated.
- Issuance requires workflow_dispatch on R8_RELEASE_REF.
- The dashboard-production GitHub Environment must restrict release branches
  and require approval by authorized reviewers.
- Signing uses RSA-SHA256 and a detached signature.
- The trusted public key must be provisioned independently of the artifact.
- The private signing key must never be committed or uploaded as an artifact.
- Receipt bytes must be signature-verified before publication.
- Any failed prerequisite returns process exit code 1.
- Receipt issuance does not assess all other dashboard production requirements.
- Historical Review-to-Canonical reconciliation requires a reviewed merge diff.
- Environment variables alone are not remote CI attestation. Trust depends on
  protected GitHub workflow execution, protected environment configuration,
  trusted signing-key custody, and protected repository review controls.

## Trust and acceptance

The repository owner must review this policy and the implementation before
committing the release baseline. Configure branch protection to require the
dashboard-verification job. Provision the dashboard-production environment
with approval rules and release-branch restrictions before adding its key.

A valid receipt attests the verification scope above for one baseline.
It does not assert authentication completeness, runtime observability,
alert persistence, load capacity, disaster recovery, or overall R8 closure.

## Artifacts

- source_manifest.json
- verification.json
- environment-pip-freeze.log
- dashboard.junit.xml
- dashboard.pytest.log
- full-suite.junit.xml
- full-suite.pytest.log
- dashboard_prod_gate.receipt.json
- dashboard_prod_gate.receipt.sig

Generated timestamps and CI metadata are provenance, not deterministic
domain outputs. Source hashes bind evidence to a specific revision; they
do not make separate verification runs byte-identical.

## Dependency and platform boundary

The initial CI configuration uses Python 3.11 and pip editable installation.
Confirm compatibility with the project's actual Python and dependency policy.
The package inventory records the environment but is not a dependency lock.
Dependency locking and immutable action pinning require the repository's
approved versions; this patch does not invent those pins.
