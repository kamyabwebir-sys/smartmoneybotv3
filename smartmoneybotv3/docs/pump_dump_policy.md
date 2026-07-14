# Pump/Dump-Like Anomaly Policy

Status: Frozen for Foundation Phase

## Purpose

The platform may detect and report suspicious relationships between wallet behavior and market behavior.

The system reports evidence-backed anomalies. It does not make legal accusations.

## Allowed Language

Use:
- suspicious.
- coordinated-looking.
- anomaly.
- pump/dump-like.
- evidence-backed.
- unusual.
- abnormal relative to configured rules.

Avoid:
- confirmed manipulation.
- fraud.
- criminal.
- guaranteed pump.
- guaranteed dump.
- certainty without evidence.

## Evidence Categories

Market evidence:
- Price acceleration.
- Volume acceleration.
- Volatility spike.
- Liquidity changes.
- Liquidity removal.
- Abrupt distribution.
- Abnormal post-launch movement.

Wallet evidence:
- Shared token interaction.
- Temporal proximity.
- Synchronized buying.
- Synchronized selling.
- Concentration increase.
- Concentration decrease.
- Launch participation overlap.
- Repeated behavior across tokens.
- Flow between related wallets.

Graph evidence:
- Direct transfer relation.
- Shared funding source.
- Shared exit destination.
- Repeated co-participation.
- Cluster-like behavior.

Source evidence:
- Data source.
- Timestamp.
- Contract/event ID.
- Rule version.
- Confidence or severity.

## Reporting Requirements

Every anomaly report should include:
- What was detected.
- Which wallets/tokens/markets are involved.
- Which evidence supports it.
- Which data is missing.
- Why the system uses suspicious wording.
- Risk/severity level if available.
- Rule version.

## Determinism Requirement

The same input data and same rule versions must produce:
- Same anomaly IDs.
- Same severity.
- Same evidence references.
- Same ordering.
- Same report view.

## AI Requirement

AI may explain an anomaly in Persian.

AI may not create the anomaly.

AI may not upgrade suspicious to confirmed.

## Threshold Policy

Thresholds must be:
- Explicit.
- Versioned.
- Tested with fixtures.
- Documented before production use.

## Legal/Safety Policy

The system is an analytical tool.

It should not present findings as legal conclusions or financial advice.
