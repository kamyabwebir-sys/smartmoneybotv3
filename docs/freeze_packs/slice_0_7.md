\# Freeze Pack — Slice 0.7

\## Audit + Replay Foundation Lock



Status: Frozen  

Phase: Foundation  

Slice: 0.7  

Prerequisite: Slice 0.6 green  

Current validation state: passed in repository test run



\---



\## Purpose



Slice 0.7 locks the deterministic audit and replay foundation contracts for the strict core.



This slice exists to establish immutable, replay-safe, content-addressable records for:



\- evidence references

\- rule hits

\- reject reasons

\- decision traces

\- replay manifests



This freeze intentionally does not introduce market-structure logic, setup logic, decisioning logic, adapters, or alerts.



The goal is to lock the domain boundary and replay/audit identity model before higher-level pipeline slices begin consuming it.



\---



\## Why this slice exists



The system target is a deterministic, replayable Smart Money pipeline:



Candles -> Structure -> Setup -> Decision -> Alert



Before structure or setup engines expand, the system needs a stable foundation for:



\- explaining why a decision happened

\- preserving replay identity across runs

\- proving deterministic equivalence of semantically identical payloads

\- making audit artifacts serializable in canonical form

\- preventing non-deterministic state leakage into core records



Slice 0.7 provides exactly that foundation and nothing more.



\---



\## Locked scope



\### Included contracts

\- `EvidenceRef`

\- `RejectReason`

\- `RuleHit`

\- `DecisionTrace`

\- `ReplayManifest`



\### Included helpers

\- `make\_decision\_trace(...)`

\- `make\_replay\_manifest(...)`



\### Included behaviors

\- deterministic content-based IDs

\- canonical serialization compatibility

\- immutable tuple-based collections

\- frozen dataclasses

\- validation of text boundaries

\- validation of Decimal-only score semantics

\- validation of UTC-aware datetime normalization

\- canonical JSON validation for `metadata\_json`

\- stable ordering normalization where semantic order must not affect identity



\---



\## Locked invariants



\### General determinism invariants

1\. No wall-clock identity generation is allowed.

2\. No `datetime.now()` may be used in these contracts.

3\. No randomness may be used.

4\. No `uuid` may be used.

5\. Identity must be content-derived via existing deterministic ID infrastructure.

6\. Equal semantic payload must produce equal ID.

7\. Relevant payload change must produce changed ID.



\### Immutability invariants

1\. Contracts are frozen dataclasses.

2\. Collection fields are tuple-only.

3\. No mutable list/set/dict state is stored as identity-bearing collection members.

4\. Normalization must occur at construction boundary.



\### Serialization invariants

1\. Contracts must remain compatible with existing `canonical\_json`.

2\. Each contract must expose a canonical payload shape through `canonical\_dict()`.

3\. `metadata\_json` in `EvidenceRef`, if present, must already be canonical JSON text.

4\. Canonical serialization of the same object must remain stable across repeated calls.



\### Numeric invariants

1\. `RuleHit.score` accepts only `Decimal` or `None`.

2\. `float` is explicitly rejected.

3\. Numeric identity-sensitive payload must remain deterministic and finite.



\### Datetime invariants

1\. Replay manifest datetime fields must be timezone-aware if provided.

2\. Datetime fields must be normalized to UTC using existing time helpers.

3\. `range\_start` must be less than or equal to `range\_end`.



\---



\## Contract lock summary



\## `EvidenceRef`

Represents a stable pointer to a piece of evidence used by audit/replay layers.



Locked fields:

\- `kind: str`

\- `ref\_id: str`

\- `label: str | None`

\- `metadata\_json: str | None`



Locked rules:

\- required text fields must be non-empty

\- optional text fields must be trimmed/non-empty if present

\- `metadata\_json`, if present, must already be canonical JSON text

\- canonical representation must be stable



\---



\## `RejectReason`

Represents a deterministic explanation for rejection.



Locked fields:

\- `code: str`

\- `message: str`

\- `evidence: tuple\[EvidenceRef, ...] = ()`



Locked rules:

\- evidence collection is tuple-only

\- evidence items must be `EvidenceRef`

\- evidence ordering is normalized for deterministic identity compatibility



\---



\## `RuleHit`

Represents a deterministic rule match.



Locked fields:

\- `rule\_code: str`

\- `summary: str`

\- `evidence: tuple\[EvidenceRef, ...] = ()`

\- `score: Decimal | None = None`



Locked rules:

\- score must be `Decimal` or `None`

\- `float` is forbidden

\- score must be finite when present

\- evidence collection is tuple-only and normalized



\---



\## `DecisionTrace`

Represents an immutable deterministic audit record for a pipeline subject at a specific stage.



Locked fields:

\- `trace\_id: str`

\- `subject\_id: str`

\- `stage: str`

\- `hits: tuple\[RuleHit, ...] = ()`

\- `rejects: tuple\[RejectReason, ...] = ()`

\- `context\_refs: tuple\[EvidenceRef, ...] = ()`



Locked identity payload:

\- `subject\_id`

\- `stage`

\- `hits`

\- `rejects`

\- `context\_refs`



Locked rules:

\- `trace\_id` must match deterministic identity payload

\- semantic equivalence must preserve `trace\_id`

\- relevant payload changes must change `trace\_id`

\- collection ordering is normalized for identity stability



\---



\## `ReplayManifest`

Represents the deterministic replay identity of an input/run context.



Locked fields:

\- `manifest\_id: str`

\- `pipeline\_version: str`

\- `input\_dataset\_hash: str`

\- `config\_hash: str`

\- `symbol: str | None`

\- `venue: str | None`

\- `timeframe: str | None`

\- `range\_start: datetime | None`

\- `range\_end: datetime | None`

\- `subject\_ids: tuple\[str, ...] = ()`

\- `notes: str | None`



Locked identity payload:

\- `pipeline\_version`

\- `input\_dataset\_hash`

\- `config\_hash`

\- `symbol`

\- `venue`

\- `timeframe`

\- `range\_start`

\- `range\_end`

\- `subject\_ids`

\- `notes`



Locked rules:

\- `manifest\_id` must match deterministic identity payload

\- `input\_dataset\_hash` changes must change `manifest\_id`

\- `config\_hash` changes must change `manifest\_id`

\- aware datetimes are accepted and normalized to UTC

\- naive datetimes are rejected

\- subject IDs are tuple-only and normalized deterministically



\---



\## Test lock expectations



Slice 0.7 is considered frozen against the following behavior classes:



\- stable `DecisionTrace.trace\_id`

\- changed `DecisionTrace.trace\_id` when relevant content changes

\- stable `ReplayManifest.manifest\_id`

\- changed `ReplayManifest.manifest\_id` when dataset hash changes

\- changed `ReplayManifest.manifest\_id` when config hash changes

\- float rejection for `RuleHit.score`

\- Decimal acceptance for `RuleHit.score`

\- rejection of naive datetime in `ReplayManifest`

\- normalization of aware datetime to UTC

\- canonical validation of `EvidenceRef.metadata\_json`

\- default empty tuple behavior for evidence fields

\- canonical serialization compatibility

\- frozen immutability expectations

\- manual invalid ID rejection



Repository result at freeze time:

\- `62 passed`



\---



\## Repository assumptions preserved



This freeze assumes the following pre-existing infrastructure remains authoritative:



\- `canonical\_json` already exists

\- `deterministic\_id` already exists

\- `ensure\_utc\_datetime` already exists

\- existing Decimal validation style remains in force

\- existing test suite remains green



This slice must not redefine those lower-layer primitives.



\---



\## Architectural boundary locked by this freeze



The core may now depend on audit/replay contracts as stable domain primitives.



However, no higher-level engine may yet assume:

\- rule taxonomy semantics

\- structure-event taxonomy semantics

\- reporting/UI schema guarantees

\- adapter input/output guarantees

\- alert payload guarantees



Only the deterministic contract boundary is frozen here.



\---



\## Out of scope



The following are explicitly out of scope for Slice 0.7:



\- candles ingestion changes

\- market structure logic

\- BOS / CHOCH

\- liquidity logic

\- FVG logic

\- setup detection

\- decision engine policy

\- alerting

\- broker/exchange adapters

\- Robinhood/Base/Solana transport integration

\- execution or order routing

\- risk engine

\- ML decisioning

\- Persian reporting layer

\- live/incremental runtime orchestration

\- fixture catalogs and golden replay corpora

\- refactor into `core/contracts`



\---



\## Risks accepted at freeze time



1\. Contract location may still be reorganized later, but semantic behavior is now frozen.

2\. Audit vocabulary is still intentionally generic; richer business taxonomy is deferred.

3\. Replay fixture corpus does not yet exist; only the contract boundary exists.

4\. This freeze does not guarantee pipeline-wide replay parity yet; it only guarantees replay identity contract semantics.



\---



\## Exit criteria for this freeze



Slice 0.7 is locked when:

1\. repository tests are green

2\. contract behavior is deterministic

3\. canonical serialization compatibility is stable

4\. UTC normalization behavior is confirmed

5\. no unrelated domain logic is introduced



All criteria satisfied at current freeze point.



\---



\## Next recommended freeze pack

Slice 0.8 — Golden Replay Fixtures



Planned purpose:

\- freeze canonical sample fixtures

\- lock replay examples for deterministic regression

\- create replay-focused golden expectations

\- avoid introducing market logic while increasing regression confidence



