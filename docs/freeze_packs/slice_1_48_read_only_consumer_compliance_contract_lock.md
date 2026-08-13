# Slice 1.48 — Read-Only Consumer Compliance Contract Lock

## Purpose
Enforce immutability and compliance on ConsumerEvidenceProjection output fields.

## Governance
- Fail-Closed: Any deviation in forbidden fields triggers immediate rejection.
- Fields Locked: trade_execution_instruction, order_intent, position_sizing.

## Scope
- Artifacts: src/smart_money/discovery/consumer.py
- Enforcement: FORBIDDEN_OUTPUT_FIELDS must be a frozenset.
