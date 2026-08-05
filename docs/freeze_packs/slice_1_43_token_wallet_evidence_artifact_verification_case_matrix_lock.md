# Slice 1.43 - Token and Wallet Evidence Artifact Verification Case Matrix Lock

Slice ID: 1.43
Slice Status: LOCKED
Matrix Status: LOCKED
Review Verdict: PASS
Promotion Gate: LOCKED
Governance Only: YES
Implementation Authority: NO
Runtime Authority: NO
Trading Authority: NO
Risk Authority: NO
ML Decision Authority: NO
Reporting Authority: NO

## Scope

This slice locks the deterministic verifier case matrix for token and wallet evidence artifacts.

It is a governance-only contract lock. It does not authorize runtime implementation, trading logic, execution logic, risk calculation, opaque ML decisioning, alert generation, reporting/UI behavior, or mutation of protected discovery registry files.

## Protected Files

The following files remain protected and must not be changed by this slice:

- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

## Verifier Case Matrix

| Case ID | Verification Case | Expected Result |
|---|---|---|
| TW-EVID-001 | Artifact file exists at the declared path. | PASS when present; FAIL when missing. |
| TW-EVID-002 | Artifact is valid JSON and parseable with deterministic tooling. | PASS when valid JSON; FAIL on parse error. |
| TW-EVID-003 | Artifact declares schema_version as a fixed string. | PASS when present and fixed; FAIL when missing or dynamic. |
| TW-EVID-004 | Artifact declares evidence_kind as token_wallet_evidence. | PASS when exact; FAIL otherwise. |
| TW-EVID-005 | Artifact declares token evidence section without runtime enrichment. | PASS when structural only; FAIL on execution-derived enrichment. |
| TW-EVID-006 | Artifact declares wallet evidence section without runtime enrichment. | PASS when structural only; FAIL on execution-derived enrichment. |
| TW-EVID-007 | Token identifiers are canonical strings. | PASS when deterministic strings; FAIL on ambiguous identifiers. |
| TW-EVID-008 | Wallet identifiers are canonical strings. | PASS when deterministic strings; FAIL on ambiguous identifiers. |
| TW-EVID-009 | Evidence timestamps, when present, are fixed UTC strings. | PASS when fixed UTC; FAIL when generated dynamically. |
| TW-EVID-010 | Evidence source references are explicit and replayable. | PASS when source references are stable; FAIL when opaque. |
| TW-EVID-011 | No trading, execution, or order intent fields are introduced. | PASS when absent; FAIL when present. |
| TW-EVID-012 | No risk scoring, exposure sizing, or portfolio action fields are introduced. | PASS when absent; FAIL when present. |
| TW-EVID-013 | No opaque ML decision output is introduced. | PASS when absent; FAIL when present. |
| TW-EVID-014 | Evidence score breakdown, if later authorized, remains explanatory only. | PASS when non-decisional; FAIL when used as decision authority. |
| TW-EVID-015 | Verification result is deterministic and replayable from the artifact bytes. | PASS when replayable; FAIL when dependent on runtime state. |

## Receipt Rules

- receipt_id must be derived from canonical JSON using SHA-256.
- canonical_payload_sha256 must match the canonical payload with receipt_id and canonical_payload_sha256 excluded.
- Temporal fields must be fixed UTC strings.
- Verifier must fail closed on missing markers, missing files, protected-file mutation, or hash mismatch.

## Authority Boundary

Analytics may only produce evidence and score breakdown in future authorized slices. This slice grants no authority for direct decisions.