# Freeze Pack — Slice 0.8
## Golden Replay Fixtures and Baseline Replay Packs

Status: Proposed for freeze  
Phase: Foundation  
Slice: 0.8  
Prerequisite: Slice 0.7 frozen and green

---

## Purpose

Slice 0.8 freezes the golden replay fixture and baseline replay pack layer for the deterministic core.

This slice does not add market logic.
It does not add structure logic.
It does not add setup logic.
It does not add decision policy logic.
It does not add adapters or alerts.

Its sole purpose is to create stable, representative, canonical replay examples and baseline pack semantics so future slices can be validated against frozen deterministic expectations.

---

## Why this slice exists

Slice 0.7 froze the audit/replay contracts.
That locked the semantic boundary, but not yet the regression corpus or baseline replay pack semantics.

Before higher-level engines are introduced, the repository needs:
- frozen replay examples
- stable canonical payload samples
- fixed expected deterministic IDs
- stable UTC normalization examples
- stable canonical metadata examples
- stable baseline replay pack identity rules

Without these fixtures and baseline packs, downstream slices may accidentally preserve type shape while drifting in semantic behavior.

Slice 0.8 exists to prevent that drift.

---

## Slice objective

Create a frozen catalog of golden replay fixtures and baseline replay pack rules that proves:

1. semantically identical normalized payloads produce the same IDs
2. meaningful payload changes produce different IDs
3. canonical serialization remains stable
4. UTC normalization behavior remains stable
5. metadata canonicalization expectations remain stable
6. tuple normalization expectations remain stable
7. baseline replay pack identity remains deterministic

---

## Scope

### In scope
- `GoldenReplayFixture` contract semantics
- `BaselineReplayPack` contract semantics
- fixture definitions for `EvidenceRef`
- fixture definitions for `RejectReason`
- fixture definitions for `RuleHit`
- fixture definitions for `DecisionTrace`
- fixture definitions for `ReplayManifest`
- golden expected IDs for representative valid cases
- stable canonical serialization snapshots or equivalent assertions
- UTC normalization fixture cases
- metadata canonical JSON fixture cases
- fixture naming and organization conventions
- baseline pack naming and identity conventions
- deterministic regression expectations

### Out of scope
- actual generation of replay market data
- execution of replays
- validation of replay data against market-derived golden outputs
- new business logic
- new structure taxonomy
- setup logic
- decision policy logic
- alert logic
- adapter logic
- execution logic
- reporting/UI work
- venue integration
- performance optimization work
- persistence layer for fixtures or packs
- CLI commands for fixture or pack management
- fixture generators that use randomness or clock time

---

## Frozen contract expectations

### GoldenReplayFixture

`GoldenReplayFixture` represents a deterministic fixture bound to a replay manifest.

Expected semantic fields:
- `fixture_id`: deterministic ID for the fixture
- `replay_manifest_id`: reference to the `ReplayManifest` this fixture is based on
- `timestamp`: UTC datetime of fixture creation or fixture definition
- `data_hash`: hash of the serialized replay data or fixture payload
- `metadata_json`: canonical JSON string for additional metadata

### BaselineReplayPack

`BaselineReplayPack` aggregates multiple golden replay fixtures for a pipeline version and configuration.

Expected semantic fields:
- `pack_id`: deterministic ID for the pack
- `pipeline_version`: version of the trading pipeline
- `config_hash`: hash of the configuration used
- `fixtures`: tuple of `GoldenReplayFixture` IDs
- `creation_timestamp`: UTC datetime of pack creation or pack definition

---

## Frozen design rules

### Fixture policy
1. Fixtures must be human-readable.
2. Fixtures must be minimal but representative.
3. Fixtures must prefer semantic clarity over volume.
4. Every fixture must exist for a deterministic reason.
5. Every golden expectation must be traceable to a frozen contract rule.

### Baseline pack policy
1. Baseline packs must use deterministic fixture ordering.
2. Baseline packs must identify the pipeline version explicitly.
3. Baseline packs must identify the configuration hash explicitly.
4. Pack IDs must be content-derived from frozen pack semantics.
5. Semantically identical normalized pack payloads must map to one expected deterministic outcome.

### Determinism policy
1. No fixture may depend on wall-clock time.
2. No fixture may depend on randomness.
3. No fixture may depend on environment-specific ordering.
4. All expected IDs must be content-derived from frozen contract semantics.
5. Equivalent normalized inputs must map to one expected deterministic outcome.

### Serialization policy
1. Golden fixtures must validate canonical serialization compatibility.
2. Baseline packs must validate canonical serialization compatibility.
3. Embedded metadata examples must use canonical JSON text.
4. Serialization expectations must be stable across repeated runs.
5. Fixtures must not rely on pretty-print formatting differences.

### Datetime policy
1. Replay manifest fixture datetimes must be timezone-aware when present.
2. Fixture and pack timestamps must normalize to UTC.
3. UTC normalization cases must be explicit.
4. Naive datetime rejection belongs in tests, not in valid golden fixture examples.
5. Range ordering expectations must be represented where relevant.

### Numeric policy
1. Score-bearing fixtures must use `Decimal`, not `float`.
2. Invalid float examples may exist in negative tests, but not as valid golden fixtures.
3. Numeric examples must be finite and deterministic.

---

## Planned fixture categories

### Category A — Minimal valid evidence fixtures
Representative cases:
- bare minimal `EvidenceRef`
- `EvidenceRef` with label
- `EvidenceRef` with canonical `metadata_json`

Purpose:
Lock the smallest valid evidence shapes and metadata expectations.

### Category B — Rule and rejection fixtures
Representative cases:
- `RejectReason` without evidence
- `RejectReason` with multiple evidence refs
- `RuleHit` without score
- `RuleHit` with Decimal score
- normalized evidence ordering examples where relevant

Purpose:
Lock deterministic identity behavior around rule/reject collections.

### Category C — Decision trace fixtures
Representative cases:
- empty `hits` and `rejects`
- populated `hits`
- populated `rejects`
- populated `context_refs`
- semantically identical payloads producing equal `trace_id`
- relevant payload change producing different `trace_id`

Purpose:
Freeze `DecisionTrace` identity semantics and collection normalization expectations.

### Category D — Replay manifest fixtures
Representative cases:
- minimal manifest
- manifest with symbol, venue, timeframe
- manifest with UTC-aware range
- manifest with timezone-aware non-UTC input that normalizes to UTC
- subject ID collection normalization examples
- changed dataset hash causing changed `manifest_id`
- changed config hash causing changed `manifest_id`

Purpose:
Freeze replay identity semantics for input scope and configuration scope.

### Category E — Baseline replay pack fixtures
Representative cases:
- minimal baseline pack
- baseline pack with one fixture ID
- baseline pack with multiple fixture IDs
- equivalent normalized fixture ordering producing stable `pack_id`
- changed pipeline version causing changed `pack_id`
- changed config hash causing changed `pack_id`
- changed fixture collection causing changed `pack_id`

Purpose:
Freeze baseline replay pack identity semantics.

### Category F — Canonical stability fixtures
Representative cases:
- repeated canonical serialization of same object
- embedded metadata already canonical
- equivalent normalized collection payloads
- stable serialization snapshots or explicit assertion equivalents

Purpose:
Guard against drift in serialization and identity-sensitive normalization.

---

## Proposed repository footprint

The exact file layout may follow repository conventions, but this slice expects artifacts equivalent to:

- replay fixture module(s)
- baseline replay pack fixture definitions
- golden expectation definitions
- regression tests bound to frozen fixture and pack cases
- short documentation describing fixture and baseline pack naming and acceptance rules

This freeze does not require a final path refactor.
It freezes semantics, not package relocation.

---

## Acceptance criteria

Slice 0.8 may be considered complete only when all items below are true:

1. A representative golden fixture catalog exists for all Slice 0.7 contracts.
2. Expected deterministic IDs are explicitly locked for chosen valid cases.
3. Baseline replay pack identity semantics are explicitly locked.
4. Canonical serialization stability is verified by regression tests.
5. UTC normalization behavior is covered by replay fixture cases.
6. Metadata canonical JSON expectations are covered by fixture cases.
7. Fixture and baseline pack names and organization are documented.
8. No higher-level market logic is introduced.
9. Repository test suite remains green.

---

## Explicit non-goals

This slice must not:
- define BOS semantics
- define CHOCH semantics
- define liquidity semantics
- define FVG semantics
- define setup semantics
- define decision acceptance policy
- define alert payload contracts
- define Solana/Base/Robinhood adapters
- define execution or routing behavior
- define risk controls
- define reporting projections
- define UI behavior

---

## Risks being controlled

Slice 0.8 is specifically intended to reduce these risks:

1. semantic regression behind unchanged types
2. replay ID drift during later engine work
3. baseline pack ID drift during later pipeline work
4. accidental serialization drift
5. datetime normalization regressions
6. metadata canonicalization regressions
7. unstable tests caused by over-broad or under-specified examples

---

## Risks explicitly accepted

1. Fixture coverage will still be selective, not exhaustive.
2. Structure/setup/decision semantics remain undefined at this stage.
3. Future business taxonomy may require additional fixture families in later slices.
4. Repository file placement may evolve as long as frozen semantics remain unchanged.

---

## Install/implementation boundary

This freeze pack is documentation only.

It does not authorize:
- implementation of Slice 0.8 in this step
- refactors outside fixture-related scope
- package namespace migration
- contract semantic changes introduced by fixture work

Implementation may begin only after this freeze is accepted.

---

## Recommended implementation shape after freeze acceptance

When implementation is allowed, it should aim for:
- small curated fixture set first
- explicit golden IDs in tests
- explicit baseline pack IDs in tests
- no random or generated fixture content
- readable fixture and pack naming
- focused regression tests tied directly to frozen invariants

The first implementation pass should stay narrow and avoid introducing any non-fixture abstractions unless clearly needed.

---

## Relationship to prior slice

Slice 0.7 froze the contract boundary.
Slice 0.8 freezes the regression corpus and baseline replay pack semantics built on top of that boundary.

That ordering is intentional:
- first freeze what the contracts mean
- then freeze examples and packs that prove the meaning
- only then allow higher-order engines to depend on them

---

## Exit recommendation

After Slice 0.8 is implemented and green, the project is in a stronger position to start the first structure-oriented freeze pack, because replay and audit regressions will have both:
- semantic contract locks
- golden example locks
- baseline pack identity locks
