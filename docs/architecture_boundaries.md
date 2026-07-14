# Architecture Boundaries

Status: Foundation placeholder for Slice 0.3 compatibility.

## Core Boundary

Core produces deterministic analytical truth from canonical inputs.

Core must not depend on:

- network access
- wall-clock time during replay
- mutable global state
- AI-generated facts
- execution side effects

## Adapter Boundary

Adapters may fetch or map external data in later slices. Adapters do not define core truth.

## Reporting Boundary

Reporting may explain deterministic outputs. Reporting must not create new domain facts.

## AI Boundary

AI may summarize and assist explanation. AI must not override reason codes, evidence, or deterministic classifications.

## Robinhood Boundary

Robinhood is tracked only as a provisional future data/integration domain until its technical surface is validated.
