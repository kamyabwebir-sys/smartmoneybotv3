# Slice 1.43 - Token and Wallet Evidence Artifact Verification Case Matrix Lock

Status: LOCKED
Scope: Governance / Evidence / Documentation Only
Verifier Mode: Fail-closed
Fast Lane Delivery: ALLOWED
Protected Paths: UNCHANGED REQUIRED

## Current Slice Scope

Slice 1.43 locks the future verification case matrix for token and wallet evidence artifacts.

This slice is governance-only. It does not implement token evidence artifact generation, wallet evidence artifact generation, wallet tracing, token tracing, token scoring, wallet scoring, trading logic, execution logic, risk calculation, opaque ML decisioning, analytics decisioning, reporting behavior, UI behavior, or artifact shape validation.

The verifier for this slice is allowed to verify governance integrity, required tokens, protected file hashes, canonical file placement, and receipt generation only.

## Target Architecture Notes

This slice supports the accepted destination architecture:

- Core
- Domain
- Application
- Adapters
- Analytics
- Reporting

No logic is added to those layers in this slice.

Analytics remains evidence-only and may produce future evidence and score breakdowns only after separate governance approval. It must not make direct trading, execution, risk, or opaque ML decisions.

## Locked Verification Case Matrix

| Case ID | Acceptance Area | Future Verifier Intent | Expected Fail-Closed Behavior | Implementation Now |
|---|---|---|---|---|
| TW-EA-001 | Artifact existence | Verify required token/wallet evidence artifact files exist at canonical paths. | Fail with `MISSING_REQUIRED_ARTIFACT` if any required artifact is absent. | Governance lock only |
| TW-EA-002 | Canonical naming | Verify artifact filenames follow locked canonical naming rules. | Fail with `NON_CANONICAL_ARTIFACT_NAME` if naming drifts. | Governance lock only |
| TW-EA-003 | Canonical hash stability | Verify artifact content hash remains stable across repeated verification. | Fail with `CANONICAL_HASH_DRIFT` if hash changes without governance approval. | Governance lock only |
| TW-EA-004 | Deterministic ordering | Verify wallet/token evidence entries are sorted deterministically. | Fail with `NON_DETERMINISTIC_ORDERING` if filesystem, insertion order, or runtime order affects output. | Governance lock only |
| TW-EA-005 | Shape compliance | Verify artifact shape matches a future locked schema without interpreting evidence meaning. | Fail with `ARTIFACT_SHAPE_VIOLATION` if required fields or structure drift. | Governance lock only |
| TW-EA-006 | Evidence-only boundary | Verify artifact contains evidence metadata only, not trading, risk, decision, or alert output. | Fail with `RUNTIME_LOGIC_LEAKAGE` if execution, risk, score-decision, or alerting logic appears. | Governance lock only |
| TW-EA-007 | Read-only governance boundary | Verify verifier reads artifacts and governance docs only. | Fail with `WRITE_SIDE_EFFECT_DETECTED` if verifier mutates repo state outside receipt generation. | Governance lock only |
| TW-EA-008 | Protected file integrity | Verify protected discovery registry files remain unchanged. | Fail with `PROTECTED_FILE_MUTATION` if protected file hashes drift. | Governance lock only |
| TW-EA-009 | Replayability metadata | Verify future artifact includes deterministic replay metadata such as source id, generated-at policy, and canonical version fields once shape is locked. | Fail with `REPLAY_METADATA_MISSING` if required replay fields are absent. | Governance lock only |
| TW-EA-010 | Scope compliance | Verify no wallet tracing, token scoring, ML inference, trading, risk, or reporting/UI leakage is introduced. | Fail with `SCOPE_GUARDRAIL_VIOLATION` on any forbidden capability. | Governance lock only |

## Fail-Closed Taxonomy

The following fail-closed labels are locked for future verifier use:

- MISSING_REQUIRED_FILE
- MISSING_REQUIRED_TOKEN
- MISSING_REQUIRED_ARTIFACT
- NON_CANONICAL_ARTIFACT_NAME
- CANONICAL_HASH_DRIFT
- NON_DETERMINISTIC_ORDERING
- ARTIFACT_SHAPE_VIOLATION
- RUNTIME_LOGIC_LEAKAGE
- WRITE_SIDE_EFFECT_DETECTED
- PROTECTED_FILE_MUTATION
- REPLAY_METADATA_MISSING
- SCOPE_GUARDRAIL_VIOLATION

## Required Governance Boundaries

No execution/trading logic
No risk calculation
No opaque ML decisioning
No reporting/UI leakage into core/domain logic
No wallet/token tracing implementation
No token/wallet tracing implementation
No token scoring implementation
No wallet scoring implementation
No artifact shape implementation in this slice
No artifact generation implementation in this slice
No runtime behavior implementation in this slice
No changes under `src/`
No changes under `tests/`

## Out-of-Scope Items

This slice does not implement:

- wallet tracing
- token tracing
- token holder graph analysis
- token scoring
- wallet scoring
- trading or execution logic
- risk calculation
- opaque ML inference
- alerting logic
- reporting/UI behavior
- artifact schema validation
- artifact shape validation
- artifact generation
- analytics decisioning
- changes under `src/`
- changes under `tests/`
- changes to protected discovery registry files

## Protected Paths

The following paths must remain unchanged:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

## Slice 1.44 Handoff

Slice 1.44 may define Token and Wallet Evidence Artifact Shape Lock after this case matrix is closed.

Slice 1.44 must remain shape/schema governance only unless a later explicit authority grant permits artifact generation or runtime verification.