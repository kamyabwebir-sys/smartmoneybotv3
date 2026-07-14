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
