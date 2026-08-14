# Architecture Boundaries

Status: Active architecture baseline

## System purpose

`smartmoneybotv3` is a deterministic, explainable, and replayable
market-structure discovery platform.

Primary pipeline:

`Candles -> Structure -> Setup -> Decision -> Alert`

The system discovers and explains market structure. It does not execute trades,
route orders, calculate position risk, or delegate domain truth to opaque ML.

## Current implemented architecture

### Canonical package

`src/smart_money` is the only canonical Python package.

Implemented areas:

- `core`: immutable contracts, deterministic IDs, canonical serialization,
  time normalization, audit traces, replay manifests, configuration locks,
  domain event envelopes, and domain errors.
- `discovery`: protected registry and read-only evidence consumer projection.
- `ingestion`: evidence/candle contracts, ingestion envelope, provider
  boundaries, an in-memory evidence ledger, pipeline orchestration, and a
  Binance mapping scaffold.

Temporary root-level modules currently contain:

- persisted evidence ledger
- replay engine
- evidence population
- deterministic market scoring
- analytics orchestration

These modules are functional but are migration debt. They must move into the
canonical package through compatibility-preserving slices.

## Target layers

### Core

Owns deterministic technical primitives shared by all layers:

- canonical serialization
- deterministic identity
- UTC normalization
- immutable/frozen helpers
- audit and replay contracts
- domain-neutral errors and event envelopes

Core must not depend on Domain, Application, Adapters, Analytics, Reporting,
network access, filesystem discovery, wall-clock time, or mutable global state.

### Domain

Owns market meaning:

- candle and market facts
- swing/pivot facts
- BOS, CHOCH, liquidity sweep, displacement, and imbalance facts
- context state
- setup candidates
- decision records and reason codes
- alert facts

Domain must remain pure, deterministic, immutable where practical, and free of
I/O, provider concepts, presentation language, and transport details.

### Application

Coordinates use cases without defining market truth:

- ingest evidence
- build a canonical replay stream
- discover structure
- evaluate setups
- create deterministic decisions
- publish alert records

Application depends on ports and Domain/Core contracts. It does not depend on
concrete providers or presentation frameworks.

### Adapters

Own external and persistence integration:

- Solana RPC/indexer mapping
- Base RPC/indexer mapping
- Robinhood L2 data mapping after its technical surface is verified
- exchange/market-data mapping
- JSON/SQLite/PostgreSQL evidence ledger implementations
- filesystem fixture stores
- outbound alert transports

Adapters map external data into canonical contracts. They never define domain
truth or write directly into Core/Domain state.

### Analytics

Produces deterministic evidence and score breakdowns:

- evidence aggregation
- explainable score components
- replay comparison
- quality/completeness metrics
- anomaly evidence

Analytics must not emit direct buy/sell/order/execution/risk/portfolio actions.

### Reporting

Projects already-determined facts for users:

- Persian reports
- alert rendering
- dashboard read models
- Telegram payloads
- audit and replay summaries

Reporting must not create new domain facts or leak into Core/Domain.

## Dependency rule

Allowed dependency direction:

`Reporting -> Application -> Domain -> Core`

`Analytics -> Domain/Core`

`Adapters -> Application ports + Domain/Core contracts`

Concrete adapters are injected into Application. Domain and Core never import
Adapters, Analytics, or Reporting.

## Protected baseline

The following Slice 0.10 files remain protected:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

Any change requires a dedicated, explicitly authorized slice.

## Non-negotiable guardrails

- No trading or order execution.
- No position sizing or risk calculation.
- No portfolio automation.
- No opaque ML decisioning.
- No hidden wall-clock or random behavior in deterministic paths.
- No dummy production ledger presented as persisted evidence.
- No reporting/UI fields in Core or Domain.
- No provider-specific objects crossing into Domain.
