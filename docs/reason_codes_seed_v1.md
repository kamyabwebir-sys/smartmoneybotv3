# Reason Codes Seed v1

Status: Seed only for Slice 0.3

Purpose: provide stable initial naming style for future deterministic decisioning and reporting.

This is not the complete registry.

## Naming Rules

- Uppercase snake case
- Stable symbolic meaning
- No Persian in code itself
- Explanation text may be Persian elsewhere
- Codes should describe why, not how to display

## Seed Codes

### Structure

- STRUCTURE_BOS_BULL
- STRUCTURE_BOS_BEAR
- STRUCTURE_CHOCH_BULL
- STRUCTURE_CHOCH_BEAR
- STRUCTURE_SWEEP_HIGH
- STRUCTURE_SWEEP_LOW
- STRUCTURE_UNCLEAR

### Context

- CONTEXT_LIQUIDITY_ABOVE
- CONTEXT_LIQUIDITY_BELOW
- CONTEXT_AT_FVG
- CONTEXT_DISPLACEMENT_PRESENT
- CONTEXT_CONFLICTING_SIGNALS

### Setup

- SETUP_CANDIDATE_VALID
- SETUP_CANDIDATE_INVALID
- SETUP_MISSING_CONFIRMATION
- SETUP_LOCATION_UNFAVORABLE

### Decision

- DECISION_VALID
- DECISION_DEFER
- DECISION_BLOCKED
- DECISION_INVALID

### Evidence / Quality

- EVIDENCE_INSUFFICIENT_HISTORY
- EVIDENCE_REFERENCE_CONFIRMED
- EVIDENCE_BREAK_CONFIRMED
- EVIDENCE_REJECTION_OBSERVED

### Risk / Caution

- RISK_LOW_CONFIDENCE
- RISK_VOLATILE_ANOMALY
- RISK_SUSPICIOUS_CLUSTER
- RISK_THIN_LIQUIDITY

## Provisional Direction Labels

These codes are naming seeds, not the final registry. Direction labels such as BULL and BEAR are provisional until directional enums are frozen in a later contract shape slice.
