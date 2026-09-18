# install_freeze_pack.ps1
# Creates the initial Freeze Pack for smartmoneybotv3.
# Safe to run multiple times. Existing files are not overwritten unless -Force is used.

param(
    [string]$ProjectName = "smartmoneybotv3",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[smartmoneybotv3] $Message" -ForegroundColor Cyan
}

function New-DirectoryIfMissing {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Write-TextFile {
    param(
        [string]$Path,
        [string]$Content
    )

    if ((Test-Path -LiteralPath $Path) -and (-not $Force)) {
        Write-Host "SKIP existing file: $Path" -ForegroundColor Yellow
        return
    }

    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-DirectoryIfMissing -Path $parent
    }

    Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
    Write-Host "WRITE $Path" -ForegroundColor Green
}

Write-Step "Creating project: $ProjectName"

$Root = Join-Path (Get-Location) $ProjectName

New-DirectoryIfMissing -Path $Root
New-DirectoryIfMissing -Path (Join-Path $Root "docs")
New-DirectoryIfMissing -Path (Join-Path $Root "src")
New-DirectoryIfMissing -Path (Join-Path $Root "src\smartmoneybot")
New-DirectoryIfMissing -Path (Join-Path $Root "src\smartmoneybot\governance")
New-DirectoryIfMissing -Path (Join-Path $Root "src\smartmoneybot\core")
New-DirectoryIfMissing -Path (Join-Path $Root "src\smartmoneybot\discovery")
New-DirectoryIfMissing -Path (Join-Path $Root "src\smartmoneybot\adapters")
New-DirectoryIfMissing -Path (Join-Path $Root "src\smartmoneybot\reporting")
New-DirectoryIfMissing -Path (Join-Path $Root "src\smartmoneybot\ai")
New-DirectoryIfMissing -Path (Join-Path $Root "tests")
New-DirectoryIfMissing -Path (Join-Path $Root "fixtures")
New-DirectoryIfMissing -Path (Join-Path $Root "scripts")

Write-Step "Writing Freeze Pack docs"

Write-TextFile -Path (Join-Path $Root "docs\scope_guardrails.md") -Content @'
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
'@

Write-TextFile -Path (Join-Path $Root "docs\build_plan.md") -Content @'
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
'@

Write-TextFile -Path (Join-Path $Root "docs\architecture_boundaries.md") -Content @'
# Architecture Boundaries

Status: Frozen for Foundation Phase

## Architecture Goal

The platform must separate deterministic analysis from data ingestion, user interfaces, AI narration, and delivery channels.

The core must be replayable from captured inputs.

## Bounded Contexts

### governance

Owns:
- Contract principles.
- Schema versions.
- Serialization rules.
- Versioning rules.
- Testing policies.
- Semantic specs.

Does not own:
- Trading logic.
- Live API calls.
- UI rendering.

### core

Owns:
- Closed candle processing.
- Market-structure events.
- Liquidity/context events.
- Setup candidates.
- Deterministic evidence.
- Replayable analysis.

Does not own:
- Network calls.
- Telegram.
- Dashboard UI.
- AI output.
- Wallet graph storage.
- Broker execution.

### discovery

Owns:
- Token discovery contracts.
- Wallet discovery contracts.
- Wallet profile.
- Wallet relationship.
- Cluster candidate.
- Suspicious coordination patterns.
- Pump/dump-like anomaly contracts.

Does not own:
- Chain-specific RPC details.
- Legal conclusions.
- AI-generated truth.
- Trading execution.

### adapters

Owns:
- External data access.
- API/RPC clients.
- File loading.
- Chain-specific mapping.
- Raw-to-canonical transformation.

Does not own:
- Core event semantics.
- Final risk truth.
- Persian narration.
- UI state.

### reporting

Owns:
- Persian user reports.
- Execution summaries.
- Error explanations.
- Risk explanation views.
- Dashboard read models.
- Telegram payload models.

Does not own:
- Domain truth.
- Core calculations.
- External API calls.
- AI decisioning.

### ai

Owns:
- Optional explanation assistance.
- Persian summarization.
- Report narration.
- User Q&A over evidence.

Does not own:
- Deterministic events.
- Risk flags.
- Wallet clusters.
- Token discovery truth.
- Trading decisions.

## Dependency Direction

Allowed:
- reporting depends on core/discovery outputs.
- ai depends on reporting/evidence outputs.
- adapters produce canonical inputs.
- core consumes canonical inputs.
- discovery consumes canonical inputs and evidence.
- dashboard consumes reporting read models.
- Telegram consumes reporting payloads.

Forbidden:
- core depends on ai.
- core depends on Telegram.
- core depends on dashboard.
- core depends on live APIs.
- core depends on wall-clock time.
- reporting creates hidden domain facts.
- ai changes deterministic scores.

## Data Flow

Typical flow:

1. Adapter captures raw external data.
2. Adapter maps raw data into canonical input contracts.
3. Core/discovery processes canonical inputs.
4. Core/discovery produces events, candidates, evidence, and risk flags.
5. Reporting creates Persian/user-facing views.
6. Dashboard and Telegram consume report views.
7. AI may explain report views without changing facts.

## Chain Boundary

Canonical contracts should be chain-agnostic when possible.

Chain-specific data belongs in:
- adapter metadata.
- chain extension fields.
- chain-specific raw snapshots.
- domain-specific mapping logic.

Chain-specific details must not leak into all contracts unless required.

## Robinhood Boundary

Robinhood is registered as:
- New Ethereum-based network/domain.
- Provisional until technical validation.
- Future adapter target.

Until validated, do not:
- Hard-code final RPC assumptions.
- Claim full EVM compatibility.
- Assume explorer/API availability.
- Implement production adapter.

## Dashboard Boundary

Dashboard is:
- A consumer of read models.
- A product layer.
- Not part of deterministic core.

The dashboard must not:
- Recalculate core truth independently.
- Mutate core analysis.
- Depend on hidden UI state for risk results.

## Telegram Boundary

Telegram is:
- A delivery adapter.
- A formatting and notification channel.

Telegram must not:
- Create risk flags.
- Change scores.
- Become required for core execution.
- Hold the only copy of reports.

## AI Boundary

AI can explain evidence.

AI cannot create or override:
- Structure events.
- Risk flags.
- Wallet clusters.
- Token discovery truth.
- Pump/dump-like anomaly truth.
- Trading decisions.

Every AI response must be grounded in deterministic evidence or clearly marked as general explanation.
'@

Write-TextFile -Path (Join-Path $Root "docs\open_questions.md") -Content @'
# Open Questions

Status: Active

This document tracks unresolved decisions. Do not guess silently. If a question affects semantics, contracts, scoring, or external integration, resolve it here before implementation.

## Robinhood Technical Surface

Current assumption:
- Robinhood is a new Ethereum-based network/domain.
- It is provisional until validated.

Open questions:
- Is it fully EVM-compatible?
- What is the chain ID?
- What RPC providers are available?
- Is there a block explorer?
- Are token contracts standard ERC-20/ERC-721/ERC-1155?
- Are there official docs?
- Are there rate limits?
- What raw data is required for discovery?
- What is the earliest safe adapter scope?

## Base Scope

Current assumption:
- Base means the Ethereum L2 network.

Open questions:
- Which RPC provider should be used?
- Which explorer/API should be used?
- Which token standards are initially supported?
- Should Base be implemented before or after Robinhood validation?

## Solana First Scope

Open questions:
- Which data provider is preferred?
- RPC only or indexer?
- Should token discovery start from launches, DEX pools, wallets, or trending data?
- Which DEX sources are initial targets?
- Which wallet behavior patterns are first?

## Market Structure Semantics

Open questions:
- Exact definition of swing high/low.
- Exact definition of BOS.
- Exact definition of CHOCH.
- Exact definition of sweep.
- Exact definition of liquidity zone.
- Exact definition of FVG/imbalance.
- Which candle timestamp represents the candle: open time or close time?
- Which timeframes are initially supported?

## Token Discovery

Open questions:
- What makes a token candidate?
- What minimum data is required?
- How is source reliability represented?
- How are scams/rug risks flagged?
- How are missing data and unknowns reported?

## Wallet Intelligence

Open questions:
- What makes a wallet "smart"?
- What evidence is required before labeling?
- How is wallet confidence calculated?
- How are related wallets detected?
- How are clusters represented?
- How are false positives reduced?

## Pump/Dump-Like Anomaly Analysis

Open questions:
- What thresholds define abnormal price/volume behavior?
- What wallet-flow timing is suspicious?
- How should liquidity exit patterns be represented?
- How should concentration changes be measured?
- How should coordinated-looking behavior be reported without overclaiming?

## Reporting

Open questions:
- What report sections are required for beginners?
- What risk levels are used?
- Should reports include recommended next actions?
- What disclaimers are required?
- How detailed should Telegram summaries be?
- What dashboard widgets are first?

## AI

Open questions:
- Which model provider is used later?
- Should the first AI interface be local, cloud, or provider-agnostic?
- What evidence format is passed to AI?
- How are AI outputs audited?
- Should AI output be stored with prompt/model/version metadata?

## Infrastructure

Open questions:
- Is SQLite enough for early local storage?
- Should DuckDB be used for analytical snapshots?
- When should a server database be introduced?
- Which job runner is acceptable on Windows?
- Which deployment target is first on Linux?
'@

Write-TextFile -Path (Join-Path $Root "docs\core_contracts_principles.md") -Content @'
# Core Contracts Principles

Status: Frozen for Foundation Phase

## Purpose

Contracts define stable data boundaries between platform components.

They must be:
- Deterministic.
- Explicit.
- Immutable.
- Versioned.
- Serializable.
- Testable.
- Explainable.

## Python Model Policy

Use:
- Python 3.11 or newer.
- dataclasses for early immutable contracts.

Recommended pattern:
```python
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

@dataclass(frozen=True, slots=True)
class ExampleContract:
schema_version: str
event_id: str
occurred_at: datetime
value: Decimal

Rules:
- Use `@dataclass(frozen=True, slots=True)`.
- Do not use mutable default values.
- Use explicit optional fields.
- Use enums where semantics matter.
- Validate invariants in constructors or factory functions.
- Keep contracts small and composable.

## Schema Version Policy

Every serializable contract must include:
- schema_version.

Breaking changes require:
- Version bump.
- Fixture update.
- Snapshot update.
- Migration note.
- Documentation update.

## ID Policy

IDs must be deterministic when used for replayable events.

Potential deterministic ID inputs:
- schema version.
- symbol/market.
- timeframe.
- event type.
- event timestamp.
- event sequence.
- canonical payload hash.

Do not use random UUIDs for deterministic domain events.

Random IDs are only allowed for external operational records where replay stability is not required.

## Numeric Policy

Use Decimal for:
- price.
- volume.
- liquidity.
- size.
- amount.
- ratio where exactness matters.
- token supply-like values when precision matters.

Use int for:
- counts.
- indexes.
- block heights.
- sequence numbers.

Avoid float in canonical contracts.

If float is unavoidable:
- Document why.
- Keep it outside canonical replay contracts if possible.
- Test serialization stability.

## Time Policy

Use timezone-aware UTC datetimes only.

Rules:
- No naive datetime.
- No local timezone in contracts.
- No wall-clock calls inside deterministic core.
- Input timestamps must be explicit.

Candle policy:
- Candles are identified by open_time.
- Candles passed to core are considered closed/complete.
- Incomplete/live candles belong outside deterministic core.

## Ordering Policy

Candles:
- Order by market, symbol, timeframe, open_time.

Events:
- Order by market, symbol, timeframe, event_time, event_type, sequence.

Wallet relations:
- Normalize node IDs.
- Order by source_node_id, target_node_id, relation_type.

Discovery candidates:
- Order by stable scoring tuple.
- Never rely on accidental insertion order.

## Serialization Policy

Canonical JSON must be stable.

Rules:
- Stable field order.
- Stable Decimal representation.
- Stable datetime representation.
- Stable enum representation.
- No non-deterministic dictionary ordering.
- No hidden fields.

Recommended datetime format:
- ISO 8601 UTC.
- Use `Z` or explicit `+00:00` consistently.

Recommended Decimal format:
- String representation.
- No binary float conversion.

## Evidence Policy

Every important conclusion should reference evidence.

Examples:
- A setup candidate references structure events and context events.
- A risk flag references source data and rule version.
- A wallet cluster references wallet relations.
- A pump/dump-like anomaly references market and wallet evidence.

Evidence should include:
- evidence_id.
- evidence_type.
- source_contract_id.
- rule_version.
- short explanation.
- confidence or severity when applicable.

## Risk Flag Policy

Risk flags must be:
- Named.
- Versioned.
- Evidence-backed.
- Explainable.
- Separated from AI narration.

Risk flags should not be hidden inside natural-language reports.

## Contract Boundary Policy

Do not mix these concepts too early:
- StructureEvent.
- ContextEvent.
- DecisionEvent.
- AlertCandidate.
- SetupCandidate.
- ReportView.

Avoid creating decision events before deterministic setup semantics are stable.

Avoid creating alert candidates before reporting and delivery boundaries are stable.

## Domain Terms Requiring Spec Before Implementation

Do not implement these until defined:
- BOS.
- CHOCH.
- sweep.
- FVG.
- liquidity zone.
- imbalance.
- smart wallet.
- suspicious cluster.
- pump/dump-like anomaly.
- token discovery candidate.
- source reliability.
'@

Write-TextFile -Path (Join-Path $Root "docs\testing_strategy.md") -Content @'
# Testing Strategy

Status: Frozen for Foundation Phase

## Testing Goals

Tests must prove:
- Determinism.
- Replayability.
- Contract invariants.
- Stable serialization.
- Cross-platform behavior.
- Clear reporting from evidence.
- No accidental network dependency in core tests.

## Test Layers

### Unit Tests

Purpose:
- Validate small functions and contracts.

Required for:
- Contract invariants.
- Timestamp validation.
- Decimal validation.
- Ordering logic.
- ID generation.
- Risk flag creation.

### Golden/Snapshot Tests

Purpose:
- Ensure canonical output does not change accidentally.

Required for:
- Contract serialization.
- Event lists.
- Setup candidates.
- Discovery candidates.
- Report views.

Rules:
- Snapshots must be deterministic.
- Snapshot changes require review.
- Snapshot changes require explanation.

### Replay Tests

Purpose:
- Ensure same input produces same output.

Replay test must verify:
- Same fixtures.
- Same rules.
- Same output IDs.
- Same ordering.
- Same reports.

### Fixture-Driven Scenario Tests

Purpose:
- Represent domain scenarios.

Examples:
- Simple candle sequence.
- BOS-like sequence after semantic definition.
- Sweep-like sequence after semantic definition.
- Token launch scenario.
- Wallet cluster scenario.
- Pump/dump-like anomaly scenario.

### Contract Validation Tests

Purpose:
- Ensure invalid objects fail early.

Examples:
- Naive datetime rejected.
- Negative volume rejected when not allowed.
- Empty symbol rejected.
- Invalid schema version rejected.
- Mutable defaults not used.

### Cross-Platform Smoke Tests

Purpose:
- Ensure Windows and Linux compatibility.

Check:
- Path handling.
- Newline handling.
- UTF-8 handling.
- PowerShell scripts.
- Python test invocation.

## Network Policy

Unit/domain/core tests:
- No network.
- No RPC.
- No live API.
- No Telegram call.
- No AI call.

Adapter tests:
- Use fixtures/mocks by default.
- Live integration tests must be explicitly marked.
- Live tests must be skipped by default.

## AI Test Policy

AI implementation is deferred.

When AI is introduced:
- Mock model outputs in tests.
- Store prompt template version.
- Store model/provider metadata.
- Verify AI cannot modify deterministic facts.
- Verify AI output references evidence.

## Reporting Test Policy

Reports should be tested through:
- Structured report models.
- Persian text snapshots for important templates.
- Evidence references.
- Error explanation scenarios.

Reports must disclose:
- What was executed.
- What data was used.
- What failed.
- What was skipped.
- Why candidates matter.
- What is unknown.
- Risk evidence.

## Pump/Dump Testing Policy

Tests must avoid overclaiming.

Expected outputs should use:
- suspicious.
- coordinated-looking.
- anomaly.
- evidence-backed.

Tests should not expect:
- confirmed manipulation.
- legal attribution.
- guaranteed prediction.

## Acceptance Rule

A feature is not complete unless it has:
- Invariant tests.
- Serialization tests if contract is serializable.
- Replay or fixture test if deterministic.
- Documentation update if semantics changed.
'@

Write-TextFile -Path (Join-Path $Root "docs\ai_policy.md") -Content @'
# AI Policy

Status: Frozen for Foundation Phase

## Decision

AI is design-in-scope early.

AI implementation is deferred until deterministic foundations stabilize.

Minimal AI interfaces may be introduced before full implementation if they do not affect deterministic truth.

## Allowed AI Uses

AI may be used for:
- Persian summarization.
- Persian explanation.
- Translation.
- Report narration.
- Error explanation.
- Beginner education.
- Q&A over generated reports.
- Clarifying uncertainty.
- Making reports easier to understand.

## Forbidden AI Uses

AI must not be the authoritative source for:
- Structure events.
- Risk flags.
- Token discovery truth.
- Wallet clustering truth.
- Pump/dump-like anomaly truth.
- Trading decisions.
- Execution decisions.
- Canonical scoring.

AI must not silently create facts that are not present in deterministic evidence.

## Evidence Grounding

Every AI-visible report should be grounded in deterministic evidence.

AI outputs should reference:
- Candidate IDs.
- Risk flags.
- Evidence items.
- Source summaries.
- Unknowns.
- Confidence/severity values when present.

## AI Output Requirements

AI-generated text should:
- Be in Persian for the user.
- Be beginner-friendly.
- Explain uncertainty.
- Avoid financial advice language.
- Avoid guaranteed outcomes.
- Avoid legal accusations.
- Distinguish facts from interpretation.

## Future AI Metadata

When AI implementation starts, store:
- provider.
- model.
- prompt template version.
- input evidence hash.
- output timestamp.
- safety policy version.

## AI Boundary Statement

AI explains the system's evidence. AI does not create the system's evidence.
'@

Write-TextFile -Path (Join-Path $Root "docs\product_capabilities.md") -Content @'
# Product Capabilities

Status: Frozen as Roadmap-Level Scope

## Product Vision

smartmoneybotv3 is intended to become a professional intelligence platform for market structure, token discovery, wallet intelligence, suspicious behavior analysis, and Persian reporting.

## Capability Groups

### Market Structure Intelligence

Capabilities:
- Candle-based deterministic analysis.
- Swing detection.
- Structure event detection.
- Liquidity/context detection.
- Setup candidate generation.
- Replayable evidence.

### Token Discovery

Capabilities:
- Token profile generation.
- Candidate detection.
- Risk flagging.
- Source reliability tracking.
- Evidence-backed scoring.
- Multi-chain extensibility.

### Wallet Intelligence

Capabilities:
- Wallet profile generation.
- Wallet behavior tracking.
- Smart wallet candidate detection.
- Wallet relationship graph.
- Wallet cluster candidates.
- Copy-trading risk awareness.

### Pump/Dump-Like Anomaly Analysis

Capabilities:
- Market behavior anomaly detection.
- Wallet-flow anomaly detection.
- Suspicious concentration shift detection.
- Coordinated-looking activity reporting.
- Evidence-backed uncertainty disclosure.

### Macro And Institutional Watch

Capabilities:
- Macro event monitoring architecture.
- Institutional watchlist architecture.
- Portfolio company monitoring architecture.
- Correlation read models later.

Not foundation priority unless required for reporting design.

### Persian Reporting

Capabilities:
- Execution summary.
- Error explanation.
- Candidate explanation.
- Risk explanation.
- Beginner-friendly educational wording.
- Unknowns and uncertainty section.

### Dashboard

Capabilities:
- Professional dashboard later.
- Candidate views.
- Risk views.
- Wallet graph views.
- Token discovery views.
- Execution history.
- Report archive.

Foundation scope:
- Read model architecture only.

### Telegram

Capabilities:
- Report summaries.
- Candidate alerts later.
- Risk notifications later.
- Error notifications.
- Daily/periodic summaries.

Foundation scope:
- Message payload architecture only.

### AI Assistant

Capabilities:
- Persian summaries.
- User Q&A over reports.
- Error explanation.
- Educational explanations.
- Risk narration.

Foundation scope:
- Policy and interface planning only.

## Capability Priority

Early:
- Foundation docs.
- Contracts.
- Deterministic core.
- Testing.
- Serialization.

Middle:
- Reporting.
- Token discovery.
- Wallet intelligence.
- Pump/dump-like anomaly contracts.

Later:
- Dashboard UI.
- Telegram bot.
- Live adapters.
- AI implementation.
- Macro/institutional watch.
'@

Write-TextFile -Path (Join-Path $Root "docs\robinhood_domain_note.md") -Content @'
# Robinhood Domain Note

Status: Provisional

## Current User Definition

Robinhood is a new Ethereum-based network/domain.

## Current Project Treatment

Robinhood is included as a priority target domain after Solana and alongside the future multi-domain architecture.

It remains provisional until technical validation is complete.

## Provisional Assumptions

Possible assumptions:
- Ethereum-based.
- Possibly EVM-compatible.
- May support token contracts.
- May need RPC/explorer/indexer access.
- May require a dedicated adapter.

These assumptions must not be treated as confirmed until validated.

## Required Validation

Before implementing a production adapter, confirm:
- Official technical documentation.
- Chain ID.
- RPC endpoints.
- Explorer availability.
- Token standards.
- Event/log semantics.
- Rate limits.
- Provider reliability.
- Data availability for wallet/token discovery.

## Adapter Rule

Do not hard-code Robinhood behavior into core contracts.

Implement Robinhood support through:
- adapters.
- chain/domain metadata.
- canonical mapping.
- fixtures.
- validation tests.

## Risk

If Robinhood semantics differ from standard EVM chains, chain-specific mapping must stay isolated in the adapter layer.
'@

Write-TextFile -Path (Join-Path $Root "docs\dashboard_telegram_policy.md") -Content @'
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
'@

Write-TextFile -Path (Join-Path $Root "docs\pump_dump_policy.md") -Content @'
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
'@

Write-TextFile -Path (Join-Path $Root "README.md") -Content @'
# smartmoneybotv3

smartmoneybotv3 is a deterministic, explainable, replayable market-structure and discovery platform with Persian-first reporting.

## Current Status

Foundation Freeze Pack installed.

No trading execution.
No live broker integration.
No AI decisioning.
No production dashboard yet.
No production Telegram bot yet.

## Initial Priorities

1. Solana.
2. Robinhood, provisional Ethereum-based network/domain.
3. Base.

## Project Layout

- docs/ - governance, planning, policies, and freeze documents.
- src/smartmoneybot/ - future Python package.
- tests/ - future tests.
- fixtures/ - deterministic input fixtures and snapshots.
- scripts/ - helper scripts.

## Next Step

Implement Slice 0.2:
- pyproject.toml
- pytest.ini
- minimal package skeleton
- smoke test
'@

Write-TextFile -Path (Join-Path $Root "FREEZE_PACK_INDEX.md") -Content @'
# Freeze Pack Index

Installed documents:

1. docs/scope_guardrails.md
2. docs/build_plan.md
3. docs/architecture_boundaries.md
4. docs/open_questions.md
5. docs/core_contracts_principles.md
6. docs/testing_strategy.md
7. docs/ai_policy.md
8. docs/product_capabilities.md
9. docs/robinhood_domain_note.md
10. docs/dashboard_telegram_policy.md
11. docs/pump_dump_policy.md

Foundation decisions:

- Project name: smartmoneybotv3.
- Reports: Persian first.
- Code/contracts: English.
- Initial environment: Windows + PowerShell.
- Later deployment: Linux server.
- Priority domains: Solana, Robinhood, Base.
- Robinhood: new Ethereum-based network/domain, provisional.
- AI: architecture and minimal interfaces allowed early, implementation deferred.
- Dashboard: in roadmap, implementation later.
- Telegram: in roadmap, implementation later.
- Pump/dump: suspicious anomaly reporting, not legal accusation.
- Core: deterministic, explainable, replayable, offline-capable.
'@

Write-Step "Writing placeholder package files"

Write-TextFile -Path (Join-Path $Root "src\smartmoneybot\__init__.py") -Content @'
"""smartmoneybotv3 package."""
'@

Write-TextFile -Path (Join-Path $Root "src\smartmoneybot\governance\__init__.py") -Content @'
"""Governance, contracts, schemas, and versioning helpers."""
'@

Write-TextFile -Path (Join-Path $Root "src\smartmoneybot\core\__init__.py") -Content @'
"""Deterministic market-structure core."""
'@

Write-TextFile -Path (Join-Path $Root "src\smartmoneybot\discovery\__init__.py") -Content @'
"""Token, wallet, graph, and anomaly discovery layer."""
'@

Write-TextFile -Path (Join-Path $Root "src\smartmoneybot\adapters\__init__.py") -Content @'
"""External data adapters and canonical mapping."""
'@

Write-TextFile -Path (Join-Path $Root "src\smartmoneybot\reporting\__init__.py") -Content @'
"""Persian reporting, dashboard read models, and Telegram payloads."""
'@

Write-TextFile -Path (Join-Path $Root "src\smartmoneybot\ai\__init__.py") -Content @'
"""AI-assisted explanation layer. Not a source of deterministic truth."""
'@

Write-Step "Freeze Pack installation complete"
Write-Host ""
Write-Host "Project created at:" -ForegroundColor White
Write-Host "  $Root" -ForegroundColor Green
Write-Host ""
Write-Host "Next recommended command:" -ForegroundColor White
Write-Host "  cd $ProjectName" -ForegroundColor Green
Write-Host ""
Write-Host "Read first:" -ForegroundColor White
Write-Host "  FREEZE_PACK_INDEX.md" -ForegroundColor Green
Write-Host "  docs\scope_guardrails.md" -ForegroundColor Green
Write-Host "  docs\build_plan.md" -ForegroundColor Green


بعد از اجرا، این ساختار ساخته می‌شود:

```text
smartmoneybotv3/
  README.md
  FREEZE_PACK_INDEX.md
  docs/
    scope_guardrails.md
    build_plan.md
    architecture_boundaries.md
    open_questions.md
    core_contracts_principles.md
    testing_strategy.md
    ai_policy.md
    product_capabilities.md
    robinhood_domain_note.md
    dashboard_telegram_policy.md
    pump_dump_policy.md
  src/
    smartmoneybot/
      governance/
      core/
      discovery/
      adapters/
      reporting/
      ai/
  tests/
  fixtures/
  scripts/
