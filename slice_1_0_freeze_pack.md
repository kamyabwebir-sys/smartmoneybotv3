# Slice 1.0 Freeze Pack - Raw Candle Ingestion

Status: BLOCKED
Implementation Authority: NONE
Approval Status: BLOCKED

## Scope

Slice 1.0 is review-preparation only until approval evidence is completed.

This freeze pack does not approve implementation, source changes, package movement,
module movement, ingestion logic, execution logic, trading logic, risk calculation,
opaque ML decisioning, reporting leakage, or UI leakage into core/domain logic.

## Review Inputs

Approval review must collect and cite evidence for:
- roadmap sequencing for Slice 1.0 after the completed foundation slices
- existing deterministic ID conventions
- existing canonical serialization conventions
- existing replay assumptions
- existing domain error/event conventions
- current test style for immutable and deterministic contracts

### Review Sequencing Note (Review-Only)

Slice 1.0 review is sequenced after the completed foundation slices 0.9, 0.10, and 0.11.
Those foundations provide deterministic ID/canonical serialization contracts, the
deterministic structure discovery registry contract, and immutable deterministic domain
event/error contracts. This sequencing note is review-only and does not approve source
changes, package/module movement, ingestion implementation, or any change to existing
event/error contracts.