# Slice 1.41 - Discovery Capability Contract Lock: Token and Wallet Evidence Artifacts

## Slice Identity

- Slice ID: slice_1_41_discovery_capability_contract_lock
- Slice Type: Governance-only
- Contract Status: CONTRACT_LOCKED
- Promotion Gate: LOCKED
- Implementation Authority: NO
- Verifier Mode: Fail-closed
- output is deterministic
- output is replayable

## Purpose

This slice locks the governance contract for future discovery capability evidence artifacts.

This slice defines the permitted shape and constraints for token evidence artifacts and wallet evidence artifacts.

This slice is a contract lock only.

## Explicit Non-Goals

The following are NOT ALLOWED in this slice:

- execution/trading logic: NOT ALLOWED
- risk calculation: NOT ALLOWED
- opaque ML decisioning: NOT ALLOWED
- reporting/UI leakage: NOT ALLOWED
- live discovery execution: NOT ALLOWED
- registry mutation: NOT ALLOWED
- exchange/broker integration: NOT ALLOWED
- Solana/Base/Robinhood network access: NOT ALLOWED
- wallet scoring decision: NOT ALLOWED
- token buy/sell/hold decision: NOT ALLOWED

## Protected Baseline

The following protected files must not be modified by this slice:

- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

Expected SHA256 values:

- src/smart_money/discovery/registry.py: 744c4cc809794efb455f209f9857ed0f89a5a97f135e872b0f014f50082742d7
- tests/discovery/test_registry.py: a68aa20a90826aed09e4bcd61837499583cac5401372a1fbc587de9b636ed26a

The verifier must fail closed if either protected file is missing, modified, untracked, or has a hash mismatch.

## Locked Capability Contract

Future discovery evidence artifacts may describe observed evidence only.

Allowed artifact categories:

- token evidence artifact
- wallet evidence artifact

Allowed artifact behavior:

- preserve deterministic identity
- preserve canonical serialization
- preserve replayable evidence fields
- expose evidence source labels
- expose score breakdown only when score components are deterministic and explainable
- provide stable reason codes
- provide stable schema version

Disallowed artifact behavior:

- direct execution decisions
- direct trading decisions
- direct risk decisions
- opaque model decisions
- mutation of discovery registry
- mutation of protected baseline files
- reporting/UI formatting inside core/domain logic

## Token Evidence Artifact Contract

A future token evidence artifact may include deterministic evidence such as:

- token identifier
- chain identifier
- observation window identifier
- deterministic artifact id
- schema version
- evidence source labels
- observed liquidity evidence
- observed holder distribution evidence
- observed activity evidence
- observed market-structure evidence
- deterministic score component breakdown
- stable reason codes

A token evidence artifact must not decide whether to buy, sell, hold, trade, execute, block, approve, or size a position.

## Wallet Evidence Artifact Contract

A future wallet evidence artifact may include deterministic evidence such as:

- wallet identifier
- chain identifier
- observation window identifier
- deterministic artifact id
- schema version
- evidence source labels
- observed token interaction evidence
- observed timing evidence
- observed clustering evidence
- observed activity evidence
- deterministic score component breakdown
- stable reason codes

A wallet evidence artifact must not decide whether a wallet is safe, unsafe, tradable, blocked, approved, or execution-worthy.

## Determinism Requirements

All future evidence artifact implementations under this contract must be deterministic.

Required deterministic properties:

- no wall-clock dependency in artifact identity
- no random identifiers
- no unordered map serialization leakage
- no environment-dependent output
- no hidden network dependency
- no non-replayable source dependency
- canonical serialization required
- stable schema version required

## Replayability Requirements

All future evidence artifact implementations under this contract must be replayable.

Required replayability properties:

- input references must be explicit
- observation window must be explicit
- evidence source labels must be explicit
- score component breakdown must be inspectable
- reason codes must be stable
- artifact identity must be reproducible from canonical inputs

## Analytics Boundary

Analytics may produce evidence and score breakdown.

Analytics must not produce direct operational decisions.

Allowed:

- evidence extraction
- deterministic score components
- explainable score breakdown
- stable reason codes

Not allowed:

- trade decision
- execution instruction
- position sizing
- risk calculation
- opaque ML decisioning

## Architecture Boundary

This slice aligns with the target architecture:

- Core / Domain / Application / Adapters / Analytics / Reporting

This slice does not require a broad refactor.

This slice does not move files between architecture layers.

This slice does not introduce runtime behavior.

## Acceptance Criteria

This slice is accepted only if:

- freeze pack exists
- evidence matrix exists
- review exists
- verifier exists
- verifier runs fail-closed
- protected registry file hash is unchanged
- protected registry test file hash is unchanged
- governance documents contain required contract tokens
- no execution/trading logic is introduced
- no risk calculation is introduced
- no opaque ML decisioning is introduced
- no reporting/UI leakage is introduced
- output is deterministic
- output is replayable

## Closure

Review Verdict: PASS-CANDIDATE

Approve as CLOSED / PASS only after the verifier succeeds.

Implementation Authority: NO
