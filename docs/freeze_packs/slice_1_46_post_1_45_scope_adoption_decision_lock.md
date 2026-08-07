# Slice 1.46 Freeze Pack
## Post-1.45 Scope Adoption Decision Lock

- Slice ID: 1.46
- Active Slice: 1.46
- Baseline Protected Slice: Slice 0.10 — Deterministic Structure Discovery Registry
- Predecessor: Slice 1.45
- Strategy: P0-B
- Decision: ACCEPTED FOR GOVERNANCE FREEZE
- Runtime Status: UNCHANGED
- Authority Status: NON-AUTHORITATIVE ARCHITECTURE RESEARCH
- Scope Type: Read-only governance lock

## 1. Objective

This Freeze Pack records the post-1.45 scope adoption decision for
SmartMoneyBotV3.

The Slice accepts architecture research as planning guidance only. It does not
authorize implementation, runtime behavior, dependency adoption, adapter work,
Core changes, Domain changes, Registry changes, Artifact Generation changes,
execution logic, risk calculation, or opaque ML decisioning.

## 2. Combined Research Conclusion

The o3 analysis and project architecture analysis converge on the same safe
direction:

- contract-first design
- canonical serialization
- deterministic IDs
- replay-first processing
- hash-based provenance
- immutable manifests and receipts
- adapter isolation
- evidence-driven analytics
- score breakdown separated from decision authority
- fail-closed governance verification

The conclusion is accepted as architecture guidance and rejected as direct
implementation authority.

## 3. Open Source Repository Classification

### NautilusTrader

Classification: P0 architectural reference.

Permitted influence:

- event-driven processing
- replay symmetry
- explicit time semantics
- data lifecycle separation
- deterministic pipeline inspiration

Forbidden adoption:

- execution engine
- order lifecycle
- portfolio management
- position management
- broker authority
- live trading orchestration

### QuantConnect Lean

Classification: P0 contract and boundary reference.

Permitted influence:

- data-source isolation
- Application and Adapter boundary patterns
- contract-heavy engine organization
- backtest/live separation as an architectural concept

Forbidden adoption:

- algorithm execution model
- portfolio engine
- brokerage implementation
- trading strategy authority
- risk behavior

### Hummingbot

Classification: P1 adapter isolation reference.

Permitted influence:

- provider isolation
- connector lifecycle concepts
- normalization boundary ideas
- market data adapter inspiration

Forbidden adoption:

- exchange execution
- order management
- trading state
- connector write access to Core or Domain

### vectorbt

Classification: P1 analytics reference.

Permitted influence:

- batch analytics
- scenario comparison
- coverage diagnostics
- evidence aggregation
- score breakdown

Forbidden adoption:

- direct decision authority
- buy or sell authority
- trade signal authority
- risk allocation
- canonical output coupling to vectorbt-specific types

### Freqtrade

Classification: P2 operational and testing reference.

Permitted influence:

- historical fixture handling
- command ergonomics
- packaging discipline
- research workflow ideas

Forbidden adoption:

- strategy execution
- order lifecycle
- portfolio state
- risk behavior

### Jesse

Classification: P2 research ergonomics reference.

Permitted influence:

- hypothesis testing workflow
- small deterministic fixtures
- research API ergonomics

Forbidden adoption:

- strategy authority
- execution semantics
- live trading behavior

### backtrader

Classification: P2 historical reference.

Permitted influence:

- event iteration concepts
- data feed and analyzer separation

Status:

- non-target architecture
- no direct dependency adoption
- no implementation authority

### smart-money-concepts

Classification: P2 vocabulary-only and candidate-rule reference.

Permitted influence:

- terms such as Swing, BOS, CHoCH, Liquidity, Order Block and FVG
- candidate structure-rule comparison

Required local authority before any future implementation:

- project-owned rule IDs
- explicit confirmation semantics
- lookback policy
- tie-break policy
- ambiguity policy
- invalid-input policy
- evidence references
- deterministic behavior

No external terminology or implementation is authoritative.

## 4. Target Architecture Notes

### Core

Core remains responsible for:

- deterministic IDs
- canonical serialization
- time semantics
- replay primitives
- low-level immutable contracts

### Domain

Domain remains responsible for:

- immutable domain models
- candle and structure semantics
- evidence-based discovery
- explicit project-owned rule contracts

### Application

Application remains responsible for:

- pipeline orchestration
- analysis requests
- manifest coordination
- replay workflow

### Adapters

Adapters remain responsible for:

- external data acquisition
- provider-specific normalization
- source isolation

Adapters must not write directly to Core or Domain state.

### Analytics

Analytics remains responsible for:

- evidence generation
- score breakdown
- diagnostics
- coverage and comparison analysis

Analytics must not issue direct buy, sell, order, execution, risk or portfolio
commands.

### Reporting

Reporting remains responsible for:

- read-only human-readable output
- Persian presentation
- evidence rendering
- provenance rendering

Reporting must not leak into Core or Domain logic.

## 5. MVP Planning Guidance

The following order is accepted as planning guidance only:

1. Contract Spine
2. Replayability
3. Evidence Capture
4. Structure Discovery
5. Analytics
6. Adapters
7. Reporting and Alerts

This ordering does not authorize implementation in Slice 1.46.

## 6. Explicitly Out of Scope

The following are forbidden in this Slice:

- Runtime implementation
- Python runtime changes
- Core changes
- Domain changes
- Registry changes
- Artifact Generation changes
- new external dependencies
- live market connectivity
- exchange integration
- broker integration
- execution or trading logic
- order lifecycle
- risk calculation
- portfolio management
- position management
- opaque ML decisioning
- setup authority
- decision authority
- reporting or UI implementation
- broad architectural refactor
- importing code from external repositories
- changing protected Slice 0.10 files

## 7. Protected Files

The following protected files must remain unchanged by this Slice:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

## 8. File Budget

Maximum primary files: 3.

Required Slice files:

1. `docs/freeze_packs/slice_1_46_post_1_45_scope_adoption_decision_lock.md`
2. `docs/governance/reviews/slice_1_46_post_1_45_scope_adoption_decision_lock_review.md`
3. `scripts/verify_slice_1_46_post_1_45_scope_adoption_decision_lock.ps1`

No additional Slice 1.46 primary file is permitted.

## 9. Acceptance Criteria

The Slice passes only when:

- all three required paths exist
- exact filenames are preserved
- Slice 1.46 file count is exactly three
- no Runtime, Core, Domain or Registry file is part of the Slice scope
- no external dependency is added
- no execution or trading logic is introduced
- no risk calculation is introduced
- no opaque ML decisioning is introduced
- Analytics remains evidence-only
- external repositories remain non-authoritative
- protected Slice 0.10 files remain unchanged by this Slice
- verifier exits successfully
- verifier output is deterministic

## 10. Decision

Decision: ACCEPT.

The research is accepted as non-authoritative architecture guidance.

Promotion to implementation requires a separate future Slice, separate Freeze
Pack, separate scope decision and separate verifier.
