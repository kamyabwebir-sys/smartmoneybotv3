# Project Roadmap
## smartmoneybotv3

Status: Active
Mode: Deterministic, replayable, greenfield
Core policy: strict core, no execution, no risk engine, no ML decisioning
Primary pipeline: Candles -> Structure -> Setup -> Decision -> Alert

---

## Delivery principles

The roadmap is intentionally ordered to protect deterministic behavior before feature breadth.

Guiding rules:
- contracts before engines
- replayability before intelligence
- canonical serialization before integration
- immutable models before orchestration
- freeze packs before slice implementation

This means the project does not move into higher-order market logic until the contract and replay foundations are stable.

---

## Scope guardrails

In scope for the current roadmap:
- deterministic domain contracts
- canonical serialization
- replay-safe identifiers
- structure/context/setup/decision pipeline contracts
- alert payload contracts
- deterministic regression fixtures
- Persian reporting as a downstream representation layer
- AI-assisted slice delivery with explicit freeze boundaries

Out of scope unless explicitly approved later:
- execution
- order routing
- broker automation
- risk engine
- portfolio management
- ML decisioning
- discretionary operator tooling inside core
- non-deterministic runtime behavior
- hidden mutable state in core domain objects

---

## Phase model

### Phase 0 — Foundation
Purpose:
Lock the domain primitives, validation rules, canonical serialization rules, and replay/audit contracts needed for later slices.

#### Slice 0.1 — Governance and documentation baseline
Status: Done

Delivered:
- build plan
- scope guardrails
- domain glossary
- core contract direction
- slice-based delivery discipline

#### Slice 0.5 — Contract skeletons
Status: Done

Delivered:
- early contract surfaces
- immutable-model direction
- boundary placeholders for future slices

#### Slice 0.6 — Validation and canonical boundaries
Status: Done

Delivered:
- canonical serialization discipline
- deterministic helper assumptions
- validation boundaries for immutable contracts
- compatibility expectations for lower-level helpers

#### Slice 0.7 — Audit and replay foundation
Status: Done / Frozen

Delivered:
- `EvidenceRef`
- `RejectReason`
- `RuleHit`
- `DecisionTrace`
- `ReplayManifest`
- deterministic trace/manfiest construction helpers

Locked behaviors:
- content-derived deterministic IDs
- tuple-only immutable collections
- frozen dataclass behavior
- canonical serialization compatibility
- canonical JSON validation for embedded metadata
- Decimal-only score acceptance
- float rejection in score-bearing contracts
- UTC-aware replay datetime normalization
- identity stability under normalized ordering

Validation at freeze point:
- `tests/test_audit_contracts.py` green
- `tests/test_replay_manifest.py` green
- repository test run: `62 passed`

Architectural effect:
Slice 0.7 freezes the audit/replay contract layer without introducing structure logic, setup logic, decision policy, adapters, alert transport, or execution concerns.

## Slice 0.8 - Golden Replay Fixtures and Baseline Replay Packs

Status: Ready for approval

Purpose:
Slice 0.8 prepares the documentation contract for golden replay fixtures and baseline replay packs.
It defines the intended governance boundary for deterministic replay examples without implementing replay execution,
fixture validation, persistence, adapters, CLI behavior, market logic, risk logic, or ML decisioning.

Scope:
- Define the documentation-level purpose of `GoldenReplayFixture`.
- Define the documentation-level purpose of `BaselineReplayPack`.
- Establish deterministic replay fixture invariants at a governance level.
- Keep exact field types, serialization rules, ID/hash algorithms, ordering behavior, storage format, and fixture payload shape unresolved until approved.
- Preserve strict separation between core contracts and reporting/UI behavior.

Canonical freeze pack:
- `docs/freeze_packs/slice_0_8.md`

Out of scope:
- Replay execution.
- Generating replay data.
- Validating live or historical outputs against golden fixtures.
- Persistence or file storage implementation.
- Adapters, external integrations, market logic, execution, risk, or ML decisioning.
- CLI commands or operational workflows.


## Phase 1 — Structure foundation
Purpose:
Introduce deterministic market-structure primitives only after replay contracts and fixtures are locked.

Planned slices in this phase may include:
- structure event taxonomy
- swing and pivot contracts
- BOS / CHOCH candidate contracts
- trend/context state contracts
- deterministic structure fixture packs

Constraints:
- no venue integration
- no alerts transport
- no execution
- no policy-side decision heuristics beyond frozen contracts

---

## Phase 2 — Setup foundation
Purpose:
Formalize setup detection contracts and deterministic setup classification.

Planned slices in this phase may include:
- setup candidate contracts
- confluence representation
- invalidation semantics
- evidence binding to structure/context
- deterministic setup fixture packs

Constraints:
- no runtime automation
- no broker/exchange integration
- no discretionary override logic in core

---

## Phase 3 — Decision foundation
Purpose:
Transform deterministic setup/context into deterministic decision artifacts.

Planned slices in this phase may include:
- decision classification contracts
- accept/reject reason expansion
- rule taxonomy stabilization
- decision fixture packs
- replay-linked decision audit enrichment

Constraints:
- no order execution
- no risk sizing engine
- no portfolio orchestration

---

## Phase 4 — Alert foundation
Purpose:
Produce deterministic alert outputs while keeping core logic separated from reporting and delivery channels.

Planned slices in this phase may include:
- alert payload contract
- alert rendering contract
- downstream reporting projection
- Persian reporting templates
- transport-agnostic alert publication interfaces

Constraints:
- no broker action
- no execution side effects
- no coupled UI logic inside core

---

## Architectural sequencing rules

The intended order is strict:

1. foundation contracts
2. validation and canonical serialization
3. audit/replay contracts
4. golden replay fixtures
5. structure contracts and fixtures
6. setup contracts and fixtures
7. decision contracts and fixtures
8. alert contracts and reporting projections

No slice should skip this ordering without an explicit freeze update.

---

## Stable assumptions currently in force

The roadmap currently assumes these repository primitives remain authoritative:
- `canonical_json`
- `deterministic_id`
- `ensure_utc_datetime`

Future slices may consume these helpers, but should not redefine their semantics unless a dedicated lower-layer freeze explicitly changes the contract.

---

## Current architectural boundary

Stable today:
- deterministic contract discipline
- immutable models
- replay-safe audit primitives
- canonical serialization expectations

Not yet stable:
- market structure taxonomy
- setup semantics
- decision taxonomy
- alert payload shape
- reporting projections
- adapter boundaries for Solana, Robinhood, Base

These areas remain intentionally unfrozen until later slices lock them.

---

## Delivery notes

Implementation should continue with freeze-pack-first discipline.

The recommended next step is:
- finalize and accept Freeze Pack for Slice 0.8
- implement Slice 0.8 fixtures only after freeze acceptance
- then move into structure-oriented slices

This ordering preserves regression confidence before market logic complexity increases.
