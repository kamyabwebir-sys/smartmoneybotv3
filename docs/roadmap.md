# Project Roadmap

Status: Active

## Current verified baseline

Implemented and tested:

- deterministic Core contracts and helpers
- audit traces and replay manifests
- golden replay fixture contracts
- protected discovery registry
- read-only discovery consumer projection
- immutable ingestion contracts and envelope
- ingestion provider/pipeline scaffolds
- in-memory evidence ledger and idempotency
- root-level persisted ledger and replay engine
- deterministic evidence scoring and analytics orchestration
- governance artifacts and verifiers through the ingestion envelope stage

Known gaps:

- root-level persistence/replay/scoring modules are not yet in the canonical
  package
- two ledger implementations expose different APIs and persistence behavior
- market-structure discovery algorithms are not implemented
- Setup, Decision, and Alert stages are not implemented
- Solana, Base, and Robinhood L2 adapters are not implemented
- reporting and alert transports are not implemented
- no real production ledger artifact is present

## Delivery principles

- contracts before engines
- replayability before intelligence
- canonical serialization before persistence/integration
- tests before implementation
- one deterministic behavior change per slice
- compatibility adapters before removing legacy imports
- evidence before completion claims

## Phase A — Repository convergence

### A1: Package and import convergence

Move root modules into `src/smart_money`:

- persistence ledger -> `adapters/persistence/json_ledger.py`
- replay engine -> `application/replay.py`
- evidence population -> `application/population.py`
- scorer -> `analytics/scoring.py`
- orchestrator -> `application/analytics.py`

Keep temporary compatibility imports for one release, then remove them.

Acceptance:

- no production Python module remains at repository root
- all tests live under `tests/`
- one canonical package is built
- same replay and score outputs before and after migration

### A2: Ledger contract convergence

Define one ledger port and explicit implementations:

- append/contains/read/count
- deterministic iteration order
- canonical JSON schema and version
- atomic persistence
- corruption and identity mismatch failures
- processed-state semantics

Acceptance:

- a single contract test suite runs against in-memory and JSON ledgers
- persisted round trips are byte-stable
- malformed or mismatched ledgers fail closed

## Phase B — Canonical market data

### B1: Candle normalization

- symbol and venue identity
- timeframe vocabulary
- timestamp semantics
- Decimal-only OHLCV
- source/provenance metadata
- duplicate and out-of-order rules

### B2: Dataset and replay slices

- canonical candle batches
- gap/overlap detection
- replay cursors and checkpoints
- baseline fixture packs for Solana, Base, and generic L2 data

## Phase C — Structure discovery

Deliver in this order:

1. swing/pivot contracts and deterministic detector
2. structure-leg construction
3. BOS candidate and confirmation rules
4. CHOCH candidate and confirmation rules
5. liquidity sweep facts
6. displacement facts
7. imbalance/FVG facts
8. context-state reducer

Every detector must provide:

- immutable output
- source candle references
- rule ID and version
- rejection reasons
- replay fixture coverage
- stable output ordering

## Phase D — Setup discovery

- setup taxonomy
- setup evidence binding
- confluence components
- invalidation facts
- setup state machine
- deterministic setup fixture packs

Setups describe evidence-backed candidates only. They do not size or execute
positions.

## Phase E — Decision records

- rule-based accept/reject/defer classification
- reason-code taxonomy
- deterministic decision traces
- evidence completeness gates
- replay-linked decision fixtures

Decision records are analytical outputs, not broker instructions.

## Phase F — Analytics

- score component contracts
- evidence quality/completeness metrics
- deterministic ranking for discovery views
- cross-replay comparison
- anomaly evidence for token/wallet activity

All score components must be explainable and individually serializable.

## Phase G — External adapters

Implement only after canonical contracts stabilize:

1. provider-agnostic adapter test kit
2. Solana read-only adapter
3. Base read-only adapter
4. Robinhood L2 adapter after protocol/API validation
5. optional exchange candle adapters

Adapters must support recorded-response replay and must not leak provider
objects into Domain.

## Phase H — Alerts and reporting

- immutable alert record
- Persian report projection
- Telegram transport adapter
- dashboard read model
- replay/audit report
- delivery idempotency

Rendering and transport stay downstream from deterministic truth.

## Phase I — Operational hardening

- dependency lock strategy
- schema migrations
- property-based tests
- mutation testing for critical rules
- performance benchmarks on fixed datasets
- structured logs and observability
- security and supply-chain review
- Linux deployment packaging
- backup/restore and ledger integrity procedures

## Definition of done for every slice

- scoped contract or freeze note
- failing test observed before implementation
- deterministic/replay test
- negative/fail-closed cases
- Ruff clean
- full Pytest clean
- PowerShell parser clean
- protected baseline unchanged
- migration/compatibility note when public imports change
- commit contains no cache, installer output, credentials, or dummy production
  evidence
