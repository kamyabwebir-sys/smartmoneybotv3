# Dashboard And Telegram Policy

Status: Frozen for Foundation Phase

## Dashboard Decision

Dashboard is in product scope.

Dashboard implementation is not in foundation scope.

Foundation includes:
- Read model planning.
- Report view contracts later.
- Candidate view models later.
- Risk view models later.
- Wallet graph view models later.

## Dashboard Boundary

Dashboard consumes:
- Report views.
- Read models.
- Snapshots.
- Evidence summaries.

Dashboard does not:
- Create deterministic events.
- Modify risk flags.
- Recalculate hidden scores.
- Depend on live state for core truth.

## Dashboard Future Areas

Potential views:
- Token discovery board.
- Wallet intelligence board.
- Wallet relationship graph.
- Pump/dump-like anomaly board.
- Market structure board.
- Risk dashboard.
- Execution history.
- Error and skipped-step logs.
- Persian report archive.

## Telegram Decision

Telegram reporting is in product scope.

Full Telegram bot implementation is not in foundation scope.

Foundation includes:
- Telegram payload planning.
- Message templates later.
- Delivery adapter boundary.

## Telegram Boundary

Telegram consumes:
- Report summaries.
- Candidate summaries.
- Error summaries.
- Risk summaries.

Telegram does not:
- Create risk.
- Create candidates.
- Change scores.
- Become required for replay.
- Hold the only copy of evidence.

## Telegram Future Message Types

Potential message types:
- Daily summary.
- New candidate summary.
- High-risk warning.
- Error report.
- Execution completed.
- Wallet cluster anomaly.
- Token anomaly.
- Pump/dump-like suspicious pattern.

## Persian Reporting Requirement

Telegram and dashboard content for the user should be Persian-first.

Technical IDs and contract names remain English.
