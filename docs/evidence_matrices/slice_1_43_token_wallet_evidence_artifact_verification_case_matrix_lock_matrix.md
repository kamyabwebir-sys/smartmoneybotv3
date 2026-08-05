# Slice 1.43 - Token and Wallet Evidence Artifact Verification Case Matrix

## Matrix Status

Matrix Status: CONTRACT_LOCKED
Promotion Gate: LOCKED
Implementation/Promotion Authority: NO

## Purpose

This matrix defines static PASS/FAIL cases for future verification of token and wallet evidence artifacts.

The matrix is evidence-shape only. It does not authorize analyzer execution, chain adapters, database integration, trading decisions, risk decisions, or opaque ML decisions.

## Cases

| Case ID | Expected | Artifact Class | Rule |
|---|---:|---|---|
| TW-EVID-001 | PASS | token | Minimal valid token evidence artifact with canonical identity, source reference, observed_at UTC timestamp, and evidence payload object. |
| TW-EVID-002 | PASS | wallet | Minimal valid wallet evidence artifact with canonical identity, source reference, observed_at UTC timestamp, and evidence payload object. |
| TW-EVID-003 | FAIL | token_or_wallet | Missing artifact_id must fail closed. |
| TW-EVID-004 | FAIL | token_or_wallet | Missing artifact_type must fail closed. |
| TW-EVID-005 | FAIL | token_or_wallet | Unsupported artifact_type must fail closed. |
| TW-EVID-006 | FAIL | token_or_wallet | Missing observed_at or equivalent event-time field must fail closed. |
| TW-EVID-007 | FAIL | token_or_wallet | Non-canonical timestamp format must fail closed. |
| TW-EVID-008 | FAIL | token_or_wallet | Missing source reference must fail closed. |
| TW-EVID-009 | FAIL | token_or_wallet | Missing evidence payload object must fail closed. |
| TW-EVID-010 | FAIL | token_or_wallet | Decision, trading, execution, or order fields must fail closed. |
| TW-EVID-011 | FAIL | token_or_wallet | Risk decision or risk authority fields must fail closed. |
| TW-EVID-012 | FAIL | token_or_wallet | Opaque ML verdict, classifier decision, or model-only decision fields must fail closed. |
| TW-EVID-013 | FAIL | token_or_wallet | Mutable or replay-unsafe fields such as generated_at_now, runtime_score, local_time, random_id, nonce, or wall_clock_time must fail closed. |
| TW-EVID-014 | PASS | token_or_wallet | Evidence-only analytics score_breakdown is allowed when non-decisional and fully explainable. |
| TW-EVID-015 | FAIL | token_or_wallet | Analytics fields that directly emit action, trade, approve, reject, buy, sell, route_order, or execute must fail closed. |

## Canonical Field Expectations

Required evidence artifact fields for valid PASS cases:

- artifact_id
- artifact_type
- subject_ref
- observed_at
- source_ref
- evidence_payload

Allowed artifact_type values for this matrix:

- token_evidence
- wallet_evidence

Allowed non-decisional analytics field:

- score_breakdown

Forbidden fields include but are not limited to:

- decision
- action
- trade
- buy
- sell
- execute
- order
- order_route
- route_order
- risk_decision
- risk_score_decision
- ml_verdict
- classifier_decision
- generated_at_now
- runtime_score
- local_time
- random_id
- nonce
- wall_clock_time

## Guardrail

Analytics may produce evidence and score breakdown only. Analytics must not produce direct decisions.