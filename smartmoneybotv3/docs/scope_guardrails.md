# Scope Guardrails

Status: Frozen for Foundation Phase
Project: smartmoneybotv3

## Mission

smartmoneybotv3 is a deterministic, explainable, replayable market-structure and discovery platform with Persian-first reporting.

It is designed to support:
- Smart Money market-structure analysis.
- Token discovery.
- Wallet intelligence.
- Wallet relationship graph analysis.
- Suspicious coordinated behavior detection.
- Pump/dump-like anomaly reporting.
- Persian beginner-friendly reports.
- Dashboard read models.
- Telegram report delivery.
- Multi-chain/domain adapters.

It does not perform order execution, portfolio auto-management, broker automation, or live trading decisions.

## Primary User Environment

Initial environment:
- Windows laptop.
- PowerShell-first workflows.
- Local development and offline replay.

Later deployment target:
- Linux server.
- Cross-platform filesystem and command assumptions.
- No Windows-only dependency inside the core.

## Language Policy

User-facing reports:
- Persian first.
- Beginner-friendly.
- Evidence-based.
- Clear about uncertainty and missing data.

Code, contracts, schemas, identifiers:
- English only.

## Initial Domain Priorities

Priority order:
1. Solana.
2. Robinhood.
3. Base.

Robinhood is treated as a new Ethereum-based network/domain, provisional until later technical validation and exact connector definition.

Base means the Ethereum L2 network.

## In Scope

Foundation and architecture:
- Deterministic core architecture.
- Contract semantics.
- Versioning rules.
- Testing strategy.
- Canonical serialization strategy.
- Cross-platform project layout.

Market structure:
- Candle normalization.
- Swing detection.
- BOS/CHOCH-like structure events after semantic definition.
- Liquidity and imbalance context after semantic definition.
- Setup candidates.
- Replayable evidence.

Discovery:
- Token discovery foundation.
- Wallet discovery foundation.
- Wallet profiles.
- Wallet relationship graph.
- Suspicious coordinated behavior analysis.
- Pump/dump-like anomaly detection and reporting.

Reporting:
- Persian execution reports.
- Persian error explanations.
- Persian risk explanations.
- Dashboard read models.
- Telegram report payloads.

AI:
- Architecture included early.
- Minimal interfaces may be introduced early.
- Implementation deferred until deterministic foundations stabilize.
- AI cannot be the source of deterministic truth.

Adapters:
- Solana adapter architecture.
- Robinhood adapter architecture, provisional.
- Base adapter architecture.
- File/fixture adapters.
- Future API/RPC boundaries.

## Out Of Scope For Foundation Phase

The following are intentionally not implemented in the foundation phase:
- Live trading.
- Order execution.
- Broker integration.
- Portfolio auto-management.
- Custody or private-key management.
- Production dashboard UI.
- Full Telegram bot.
- Live alerting dependency inside core.
- AI-generated trading decisions.
- Non-deterministic risk flags.
- Unbounded "latest methods" claims.
- Social scraping without explicit adapter and data contract.
- Legal attribution of manipulation.

## Non-Negotiable Core Rules

The deterministic core must not depend on:
- Live APIs.
- Wall-clock execution time.
- Randomness.
- Non-versioned model outputs.
- Hidden mutable state.
- Network availability.
- UI state.
- Telegram state.
- AI outputs.

Every important output must be explainable from explicit input data and versioned rules.

## Product Claim Policy

Allowed:
- The platform supports pluggable discovery methods.
- The platform can add new wallet/token/on-chain heuristics over time.
- The platform reports suspicious, evidence-backed patterns.

Not allowed:
- "Always finds the newest opportunities."
- "Detects manipulation with certainty."
- "AI decides what to buy."
- "Guaranteed pump/dump prediction."
- "Guaranteed profitable trading signals."

## Pump/Dump Wording Policy

Use:
- suspicious.
- coordinated-looking.
- anomaly.
- evidence-backed pattern.
- pump/dump-like behavior.

Avoid:
- guaranteed manipulation.
- confirmed fraud.
- certain pump.
- certain dump.
- accusation without evidence.

## Freeze Rule

Before adding a new major feature, create or update:
- Scope statement.
- Contract semantics.
- Adapter boundary.
- Test fixture plan.
- Reporting impact.
- Open questions.
