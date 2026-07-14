\# Slice 0.7 Domain Contracts

\## Audit + Replay Foundation



\## Goal

Introduce deterministic audit and replay contracts without adding any market logic, adapters, alerts, or structure engines.



This slice adds immutable domain contracts for:



\- Evidence references

\- Rule hits

\- Reject reasons

\- Decision traces

\- Replay manifests



These contracts support:



\- canonical serialization compatibility

\- deterministic content-based IDs

\- replay reproducibility

\- audit trail persistence

\- strict validation boundaries



\---



\## Scope



\### Included

\- `EvidenceRef`

\- `RejectReason`

\- `RuleHit`

\- `DecisionTrace`

\- `ReplayManifest`

\- `make\_decision\_trace(...)`

\- `make\_replay\_manifest(...)`

\- tests for determinism, immutability, UTC normalization, and canonical compatibility



\### Explicitly Excluded

\- market structure logic

\- BOS / CHOCH / liquidity / FVG logic

\- adapters

\- alerts

\- broker integration

\- reporting/UI logic

\- refactor into `core/contracts`

\- execution logic

\- risk logic

\- ML decisioning



\---



\## Core Design Rules



\### 1. Deterministic identity only

All IDs must be derived from content using `deterministic\_id(...)`.



Forbidden:

\- `datetime.now()`

\- randomness

\- `uuid`

\- hidden mutable state



\### 2. Immutable contracts

All contracts are:

\- frozen dataclasses

\- slot-based

\- tuple-only for collections



\### 3. Canonical serialization compatibility

All contracts expose `canonical\_dict()` and must be serializable by existing `canonical\_json(...)`.



\### 4. Validation at contract boundary

Validation happens in `\_\_post\_init\_\_` and helper constructors.



\### 5. No float acceptance for identity-sensitive numeric values

`RuleHit.score` accepts only:

\- `Decimal`

\- `None`



Float is rejected.



\---



\## Contract Summary



\## EvidenceRef

Represents a stable reference to evidence used in audit or replay.



Fields:

\- `kind: str`

\- `ref\_id: str`

\- `label: str | None`

\- `metadata\_json: str | None`



Rules:

\- `kind` must be non-empty

\- `ref\_id` must be non-empty

\- `label`, if present, must be non-empty after trim

\- `metadata\_json`, if present, must already be canonical JSON text



\---



\## RejectReason

Represents a deterministic rejection explanation.



Fields:

\- `code: str`

\- `message: str`

\- `evidence: tuple\[EvidenceRef, ...] = ()`



Rules:

\- `code` non-empty

\- `message` non-empty

\- `evidence` must be tuple-only

\- evidence entries are normalized deterministically



\---



\## RuleHit

Represents a deterministic rule match.



Fields:

\- `rule\_code: str`

\- `summary: str`

\- `evidence: tuple\[EvidenceRef, ...] = ()`

\- `score: Decimal | None = None`



Rules:

\- `rule\_code` non-empty

\- `summary` non-empty

\- `evidence` tuple-only

\- `score` must be `Decimal` or `None`

\- float is forbidden

\- score must be finite



\---



\## DecisionTrace

Represents a deterministic audit record for a subject at a pipeline stage.



Fields:

\- `trace\_id: str`

\- `subject\_id: str`

\- `stage: str`

\- `hits: tuple\[RuleHit, ...] = ()`

\- `rejects: tuple\[RejectReason, ...] = ()`

\- `context\_refs: tuple\[EvidenceRef, ...] = ()`



Rules:

\- all text fields non-empty

\- collections must be tuples

\- contents normalized deterministically

\- `trace\_id` must match deterministic payload identity



Identity payload:

\- subject\_id

\- stage

\- hits

\- rejects

\- context\_refs



\---



\## ReplayManifest

Represents deterministic replay input identity.



Fields:

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



Rules:

\- required text fields non-empty

\- optional text fields normalized

\- datetimes must be timezone-aware

\- datetimes normalized to UTC via `ensure\_utc\_datetime(...)`

\- `range\_start <= range\_end`

\- `subject\_ids` tuple-only and deterministically sorted

\- `manifest\_id` must match deterministic payload identity



Identity payload:

\- pipeline\_version

\- input\_dataset\_hash

\- config\_hash

\- symbol

\- venue

\- timeframe

\- range\_start

\- range\_end

\- subject\_ids

\- notes



\---



\## Helper Constructors



\## `make\_decision\_trace(...)`

Creates a valid `DecisionTrace` by:

\- validating inputs

\- normalizing tuple ordering

\- building deterministic payload

\- generating `trace\_id`



\## `make\_replay\_manifest(...)`

Creates a valid `ReplayManifest` by:

\- validating inputs

\- normalizing aware datetimes to UTC

\- sorting subject IDs

\- generating deterministic `manifest\_id`



\---



\## Test Intent



The tests cover:



\- stable `DecisionTrace.trace\_id`

\- changed trace ID when relevant content changes

\- stable `ReplayManifest.manifest\_id`

\- changed manifest ID when `input\_dataset\_hash` changes

\- changed manifest ID when `config\_hash` changes

\- float rejection for `RuleHit.score`

\- Decimal acceptance for `RuleHit.score`

\- naive datetime rejection for `ReplayManifest`

\- UTC normalization for aware datetime

\- canonical validation for `EvidenceRef.metadata\_json`

\- default empty tuple behavior for evidence fields

\- canonical serialization compatibility



\---



\## Acceptance Criteria



This slice is accepted when:



1\. contracts import successfully

2\. helper constructors generate deterministic IDs

3\. invalid manual IDs are rejected

4\. float score is rejected

5\. naive datetimes are rejected

6\. aware datetimes are normalized to UTC

7\. canonical serialization remains stable

8\. no unrelated project files are modified

9\. no market logic is introduced



\---



\## Notes

This slice is foundation-only.



It is intentionally limited to audit/replay contracts and deterministic validation boundaries.



