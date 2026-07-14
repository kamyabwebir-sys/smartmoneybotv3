# Build Plan

Status: Frozen for Foundation Phase

## Build Method

The project is built through small slices.

Every slice must define:
- Scope.
- Files.
- Out of scope.
- Implementation steps.
- Tests.
- Acceptance criteria.
- Next slice.

No slice should silently expand into unrelated product areas.

## Phase 0 - Foundation And Guardrails

Goal:
Create the project governance documents, architecture boundaries, contract principles, and testing strategy before implementation.

### Slice 0.1 - Project Freeze Pack

Files:
- docs/scope_guardrails.md
- docs/build_plan.md
- docs/architecture_boundaries.md
- docs/open_questions.md
- docs/core_contracts_principles.md
- docs/testing_strategy.md
- docs/ai_policy.md
- docs/product_capabilities.md
- docs/robinhood_domain_note.md
- docs/dashboard_telegram_policy.md
- docs/pump_dump_policy.md

Acceptance criteria:
- Mission is explicit.
- Scope is bounded.
- AI policy is constrained.
- Robinhood is registered as provisional Ethereum-based network/domain.
- Dashboard and Telegram are roadmap capabilities, not core dependencies.
- Pump/dump reporting language is evidence-based and non-accusatory.

### Slice 0.2 - Project Skeleton

Files:
- pyproject.toml
- pytest.ini
- src/smartmoneybot/
- tests/
- fixtures/
- scripts/

Acceptance criteria:
- Python package imports.
- pytest runs.
- No live network required.
- Cross-platform paths.

### Slice 0.3 - Core Contract Semantics Spec

Goal:
Define domain words before coding contracts.

Topics:
- Candle.
- Symbol.
- Timeframe.
- Market.
- BOS.
- CHOCH.
- Sweep.
- FVG.
- Liquidity zone.
- Setup candidate.
- Context event.
- Structure event.
- Risk flag.
- Evidence item.

Acceptance criteria:
- Each term has a semantic definition.
- Each term has input/output boundaries.
- Ambiguous terms are moved to open questions.

### Slice 0.4 - Immutable Core Contracts

Goal:
Implement minimal immutable contracts.

Rules:
- dataclasses with frozen=True and slots=True.
- Decimal for price/size-like fields.
- UTC-aware datetime.
- Explicit schema version.
- Deterministic IDs where required.

Acceptance criteria:
- Unit tests for invariants.
- Serialization tests.
- No mutable defaults.
- No network.

### Slice 0.5 - Canonical Serialization

Goal:
Stable JSON output for snapshots and replay.

Acceptance criteria:
- Field order is stable.
- Decimal serialization is stable.
- datetime serialization is stable.
- Golden files are reproducible.

## Phase 1 - Market Structure Core

Goal:
Build deterministic Smart Money market-structure analysis over closed candles.

Slices:
- Candle normalization.
- Swing detection.
- Structure event generation.
- Liquidity context.
- Imbalance/FVG context.
- Setup candidate generation.
- Replay and explanation.

Rules:
- No trading execution.
- No live API dependency.
- No AI dependency.
- Fixture-driven tests.

## Phase 2 - Persian Reporting And Explainability

Goal:
Turn deterministic evidence into beginner-friendly Persian reports.

Slices:
- Execution report schema.
- Error explanation schema.
- Risk explanation schema.
- Candidate report template.
- Telegram payload model.
- Dashboard read model.

Rules:
- Reporting consumes evidence.
- Reporting does not create domain truth.
- Persian wording must disclose uncertainty.

## Phase 3 - Token Discovery Foundation

Goal:
Create contracts and deterministic heuristics for token discovery.

Slices:
- Token profile contract.
- Discovery candidate contract.
- Evidence model.
- Risk flag model.
- Source reliability model.
- Fixture-based candidate examples.

Rules:
- No guarantee of profitability.
- No hidden scoring.
- Every score must be explainable.

## Phase 4 - Wallet Intelligence Foundation

Goal:
Create wallet profiles, wallet events, and wallet graph foundation.

Slices:
- Wallet identity contract.
- Wallet activity event.
- Wallet profile.
- Wallet relationship.
- Cluster candidate.
- Smart wallet candidate.
- Suspicious coordination event.

Rules:
- Wallet labels must include evidence and confidence.
- Avoid definitive claims without data.
- Graph logic must be replayable.

## Phase 5 - Pump/Dump-Like Anomaly Analysis

Goal:
Detect and report suspicious coordination between wallets and market behavior.

Evidence categories:
- Temporal proximity.
- Shared token interaction.
- Concentration changes.
- Synchronized flows.
- Launch participation overlap.
- Liquidity exit timing.
- Abnormal distribution timing.
- Price/volume acceleration.

Rules:
- Report anomalies, not legal conclusions.
- Use evidence and uncertainty.
- Keep thresholds versioned.

## Phase 6 - Multi-Domain Adapters

Goal:
Map external data into canonical platform contracts.

Adapters:
- Solana.
- Robinhood provisional Ethereum-based domain.
- Base.
- File fixtures.
- Future APIs.

Rules:
- Adapters may be non-deterministic at ingestion time.
- Core processing over captured input must be deterministic.
- Raw data snapshots must be versioned when used in tests.

## Phase 7 - Dashboard And Telegram

Goal:
Expose reports and read models to users.

Dashboard:
- Professional UI later.
- Read-model driven.
- No direct core dependency on UI.

Telegram:
- Delivery adapter.
- Message formatting.
- Report summaries.
- No domain authority.

## Phase 8 - AI Assistant Layer

Goal:
Help users understand results in Persian.

Allowed:
- Summarization.
- Translation.
- Report narration.
- Error explanation.
- Q&A over generated reports.

Not allowed:
- Source of deterministic events.
- Source of risk truth.
- Source of wallet cluster truth.
- Source of trading decisions.

## Slice Discipline

A slice is rejected if:
- It adds live execution.
- It adds AI decisioning.
- It adds network dependency to core.
- It changes contract semantics without updating docs.
- It adds scoring without tests and explanation.
- It adds UI before read models.
