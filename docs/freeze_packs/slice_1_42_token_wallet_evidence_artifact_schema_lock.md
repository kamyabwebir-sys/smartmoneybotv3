# Slice 1.42 — Token and Wallet Evidence Artifact Schema Lock

## Slice Metadata
- Slice ID: 1.42
- Title: Token and Wallet Evidence Artifact Schema Lock
- Type: Governance-only / Contract Lock
- Status Target: CLOSED / PASS
- Implementation Authority: NO
- Runtime Authority: NO
- Registry Mutation Authority: NO

## Objective
Lock the evidence artifact schema for token and wallet subjects as a deterministic, replayable, read-only, evidence-only contract for future consumers.

## Scope
This slice locks schema and governance expectations only.

## Locked Schema
- `schema_version: token_wallet_evidence_artifact.v1`
- `artifact_type: evidence_artifact`
- `subject_type: TOKEN | WALLET`
- `subject_id: deterministic string`
- `chain`
- `consumer_version`
- `registry_snapshot_id`
- `registry_entry_id`
- `evidence_refs`
- `deterministic_score_breakdown` (optional)
- `replay_manifest_ref`
- `boundary_status`
- `generated_from`

## Required Constraints
- Evidence-only
- Deterministic
- Replayable
- Read-only
- Boundary-safe
- Auditable
- Narrow

## Boundary Status Values
- `BOUNDARY_SAFE`
- `BOUNDARY_BLOCKED`
- `EVIDENCE_INCOMPLETE`
- `REPLAY_REFERENCE_MISSING`

## Forbidden Semantics
The locked artifact MUST NOT contain or imply:
- trade execution instruction
- order intent
- position sizing
- stop loss calculation
- take profit calculation
- risk score used as a decision
- opaque ML decision
- reporting/UI formatted payload
- direct promotion verdict
- buy
- sell
- hold
- trade_signal
- risk_value
- decision

## Protected Paths
The following protected paths MUST remain unchanged from the locked reference hashes:
- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

## Reference Protected Hashes
- `src/smart_money/discovery/registry.py` -> `744c4cc809794efb455f209f9857ed0f89a5a97f135e872b0f014f50082742d7`
- `tests/discovery/test_registry.py` -> `a68aa20a90826aed09e4bcd61837499583cac5401372a1fbc587de9b636ed26a`

## Out of Scope
- generator
- token scanner
- wallet scanner
- Solana adapter
- Base adapter
- Robinhood adapter
- registry mutation
- discovery runtime
- execution logic
- trading logic
- risk calculation
- promotion logic
- reporting/UI payload shaping
- opaque ML

## Acceptance Criteria
- Freeze pack exists
- Evidence matrix exists
- Review exists
- Verifier exists
- Required schema tokens are present in governance docs
- Forbidden semantics are explicitly blocked
- Protected path hashes match locked references
- Receipt is emitted as valid JSON
- Verifier fails closed on any mismatch