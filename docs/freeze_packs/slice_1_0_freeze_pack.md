# Freeze Pack: Slice 1.0 - Raw Candle Ingestion Contracts

Status: BLOCKED
Implementation Authority: NONE
Approval Status: BLOCKED

## Review Preparation: Candidate Invariants and Open Questions

This section records candidate invariants and review questions for Slice 1.0.
It does not approve source changes, test changes, package creation, module placement,
class names, field names, serialization APIs, ID algorithms, validation behavior,
or error-contract implementation.

### Candidate Invariant Areas for Review

The approval review must evaluate whether Slice 1.0 requires invariants in these areas:

- raw candle identity and deterministic replay compatibility
- timestamp representation and ordering assumptions
- OHLCV value representation and invalid-value handling
- canonical serialization compatibility
- source/provenance representation
- validation and error-contract alignment
- fixture strategy for valid and invalid raw candle examples

These areas are evidence targets only. They are not approved contract decisions.

### Required Evidence Before Approval

Approval review must collect and cite evidence for:

- roadmap sequencing for Slice 1.0 after the completed foundation slices
- existing deterministic ID conventions
- existing canonical serialization conventions
- existing replay assumptions
- existing domain error/event conventions
- current test style for immutable and deterministic contracts

Evidence collection alone is insufficient for approval.

### Candidate Review Questions

The approval review must answer the following before implementation can be authorized:

- Where, if anywhere, should raw candle contracts live?
- What is the minimum contract shape required for raw candle ingestion?
- Which fields are identity-bearing, if any?
- Which timestamp unit and timezone assumptions are allowed?
- Which numeric representation is deterministic enough for OHLCV values?
- Which validation failures become domain errors?
- Which examples are required as golden fixtures?
- Which behavior belongs to Slice 1.0 versus Slice 1.1 normalization?

### Explicit Non-Approval

This section does not approve:

- `RawCandle` as a final class name
- `candle_id` as a required field
- any deterministic ID formula
- any serialization method name
- any ingestion package or module path
- any error class or manifest shape
- any fixture file layout
- any source or test implementation

Final state remains BLOCKED until a separate approval review explicitly changes it.

## Review Preparation: Candidate Invariants and Open Questions

Status: REVIEW PREPARATION ONLY
Implementation Authority: NONE
Approval Status: BLOCKED

This section records candidate invariants and review questions for Slice 1.0.
It does not approve source changes, test changes, package creation, module placement,
class names, field names, serialization APIs, ID algorithms, validation behavior,
or error-contract implementation.

### Candidate Invariant Areas for Review

The approval review must evaluate whether Slice 1.0 requires invariants in these areas:

- raw candle identity and deterministic replay compatibility
- timestamp representation and ordering assumptions
- OHLCV value representation and invalid-value handling
- canonical serialization compatibility
- source/provenance representation
- validation and error-contract alignment
- fixture strategy for valid and invalid raw candle examples

These areas are evidence targets only. They are not approved contract decisions.

### Required Evidence Before Approval

Approval review must collect and cite evidence for:

- roadmap sequencing for Slice 1.0 after the completed foundation slices
- existing deterministic ID conventions
- existing canonical serialization conventions
- existing replay assumptions
- existing domain error/event conventions
- current test style for immutable and deterministic contracts

Evidence collection alone is insufficient for approval.

### Candidate Review Questions

The approval review must answer the following before implementation can be authorized:

- Where, if anywhere, should raw candle contracts live?
- What is the minimum contract shape required for raw candle ingestion?
- Which fields are identity-bearing, if any?
- Which timestamp unit and timezone assumptions are allowed?
- Which numeric representation is deterministic enough for OHLCV values?
- Which validation failures become domain errors?
- Which examples are required as golden fixtures?
- Which behavior belongs to Slice 1.0 versus Slice 1.1 normalization?

### Explicit Non-Approval

This section does not approve:

- `RawCandle` as a final class name
- `candle_id` as a required field
- any deterministic ID formula
- any serialization method name
- any ingestion package or module path
- any error class or manifest shape
- any fixture file layout
- any source or test implementation

Final state remains BLOCKED until a separate approval review explicitly changes it.

## Review Preparation: Candidate Invariants and Open Questions

Status: REVIEW PREPARATION ONLY
Implementation Authority: NONE
Approval Status: BLOCKED

This section records candidate invariant areas and review questions for Slice 1.0.
It does not approve source changes, test changes, package creation, module placement,
class names, field names, serialization APIs, ID algorithms, validation behavior,
or error-contract implementation.

### Candidate Invariant Areas for Review

The approval review must evaluate whether Slice 1.0 requires invariants in these areas:

- raw candle identity and deterministic replay compatibility
- timestamp representation and ordering assumptions
- OHLCV value representation and invalid-value handling
- canonical serialization compatibility
- source/provenance representation
- validation and error-contract alignment
- fixture strategy for valid and invalid raw candle examples

These areas are evidence targets only. They are not approved contract decisions.

### Required Evidence Before Approval

Approval review must collect and cite evidence for:

- roadmap sequencing for Slice 1.0 after the completed foundation slices
- existing deterministic ID conventions
- existing canonical serialization conventions
- existing replay assumptions
- existing domain error/event conventions
- current test style for immutable and deterministic contracts

Evidence collection alone is insufficient for approval.

### Candidate Review Questions

The approval review must answer the following before implementation can be authorized:

- Where, if anywhere, should raw candle contracts live?
- What is the minimum contract shape required for raw candle ingestion?
- Which fields are identity-bearing, if any?
- Which timestamp unit and timezone assumptions are allowed?
- Which numeric representation is deterministic enough for OHLCV values?
- Which validation failures become domain errors?
- Which examples are required as golden fixtures?
- Which behavior belongs to Slice 1.0 versus Slice 1.1 normalization?

### Explicit Non-Approval

This section does not approve:

- `RawCandle` as a final class name
- `candle_id` as a required field
- any deterministic ID formula
- any serialization method name
- any ingestion package or module path
- any error class or manifest shape
- any fixture file layout
- any source or test implementation

Final state remains BLOCKED until a separate approval review explicitly changes it.
