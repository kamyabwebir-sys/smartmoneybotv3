# Slice 1.17 - EM-003 Separate Promotion Authority Request Gate

## Status

PROPOSED

## Slice Type

Governance-only authority request gate.

## Purpose

Slice 1.17 defines a deterministic, replayable, fail-closed governance gate for evaluating whether EM-003 is ready to request separate human promotion authority.

This slice does not promote EM-003.

This slice does not unlock the EM-003 promotion gate.

This slice does not grant implementation authority.

This slice does not modify source code, tests, protected registry files, or runtime behavior.

## Current Authoritative Position

EM-003 remains PARTIAL.

Promotion remains LOCKED.

Implementation authority remains NONE.

Approval status remains NOT_APPROVED.

The current known evidence artifact is not sufficient for a separate promotion authority request because the evidence case population is empty or incomplete.

## Governance Background

Slice 1.14 granted limited future implementation authority to Slice 1.15 only.

That limited authority does not transfer to Slice 1.17.

Slice 1.17 may only evaluate request-readiness under governance-only constraints.

Any future promotion requires a separate explicit approved authority action.

## Inputs

The Slice 1.17 gate may read the following governance and evidence materials:

- artifacts/discovery/em003/evidence_report.json
- artifacts/discovery/em003/attachment_register.json, if present
- docs/freeze_packs/slice_1_5_em_003_acceptance_criteria_lock.md
- docs/freeze_packs/slice_1_6_em_003_verifier_case_matrix_lock.md
- docs/freeze_packs/slice_1_7_em_003_evidence_report_shape_lock.md
- docs/freeze_packs/slice_1_8_em_003_promotion_gate_lock.md
- docs/freeze_packs/slice_1_14_em_003_limited_verifier_authority_grant.md
- docs/reviews/slice_1_14_em_003_authority_grant_review.md
- docs/reviews/slice_1_16_em_003_evidence_result_adjudication_review.md, if present

## Allowed Actions

Slice 1.17 may:

- read locked governance materials
- read generated EM-003 evidence artifacts
- classify whether a separate authority request is blocked or request-ready
- produce a governance-only review
- produce a governance-only verifier script
- fail closed on missing, ambiguous, partial, contradictory, or unauthorized evidence state

## Forbidden Actions

Slice 1.17 must not:

- modify files under src/
- modify files under tests/
- modify protected registry files
- change EM-003 status
- unlock the EM-003 promotion gate
- grant implementation authority
- approve EM-003
- reinterpret indirect evidence as direct evidence
- introduce execution logic
- introduce trading logic
- introduce risk calculation
- introduce opaque ML decisioning
- leak reporting or UI concerns into core or domain logic

## Protected Paths

The following paths remain protected and must not be modified by this slice:

- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

In addition, Slice 1.17 must not modify any path under:

- src/
- tests/

## Deterministic Verdicts

The Slice 1.17 review must contain exactly one of the following verdicts:

- AUTHORITY_REQUEST_DENIED_FAIL_CLOSED
- AUTHORITY_REQUEST_READY_FOR_SEPARATE_HUMAN_APPROVAL

Neither verdict changes EM-003 status.

Neither verdict unlocks the promotion gate.

Neither verdict grants implementation authority.

## Decision Rules

The verdict must be AUTHORITY_REQUEST_DENIED_FAIL_CLOSED if any of the following conditions are true:

- evidence_report.json is missing
- evidence_report.json is not valid JSON
- evidence_report.json em_id is not EM-003
- evidence_report.json status is not PARTIAL
- evidence_report.json promotion_gate is not LOCKED
- evidence_report.json implementation_authority is not NONE
- evidence_report.json approval_status is not NOT_APPROVED
- evidence_report.json cases is missing
- evidence_report.json cases is empty
- any required verifier case is missing
- any required verifier case is partial
- any required governance mapping is missing
- deterministic evidence is missing or false
- replayable evidence is missing or false
- the review fails to state governance-only
- the review fails to state EM-003 remains PARTIAL
- the review fails to state Promotion remains blocked or Promotion remains LOCKED
- unauthorized source, test, or protected registry changes are present
- ambiguous approval or promotion language is present

The verdict may be AUTHORITY_REQUEST_READY_FOR_SEPARATE_HUMAN_APPROVAL only if all locked governance conditions are satisfied, all required cases are present, all required cases are non-partial, deterministic and replayable evidence is complete, and the result remains governance-only.

## Current Expected Verdict

Given the current known evidence posture, the expected verdict is:

AUTHORITY_REQUEST_DENIED_FAIL_CLOSED

Rationale:

- EM-003 remains PARTIAL.
- Promotion remains LOCKED.
- Implementation authority remains NONE.
- Approval status remains NOT_APPROVED.
- Evidence case population is empty or incomplete.

## Acceptance Criteria

Slice 1.17 is accepted only if:

- the freeze pack exists
- the review exists
- the verifier script exists
- the review explicitly states governance-only
- the review explicitly states EM-003 remains PARTIAL
- the review explicitly states Promotion remains blocked or Promotion remains LOCKED
- the review contains exactly one allowed deterministic verdict
- the verifier fails closed on missing evidence_report.json
- the verifier fails closed on invalid evidence_report.json
- the verifier fails closed on any non-PARTIAL EM-003 status
- the verifier fails closed on any unlocked promotion gate
- the verifier fails closed on any implementation authority other than NONE
- the verifier fails closed on any approval status other than NOT_APPROVED
- the verifier fails closed when evidence cases are empty unless the review verdict is AUTHORITY_REQUEST_DENIED_FAIL_CLOSED

## Final Governance Position

Slice 1.17 is a request-readiness gate only.

Separate authority request readiness is not promotion.

EM-003 remains PARTIAL.

Promotion remains blocked.

Any future promotion requires a distinct, explicit, separately approved authority action.