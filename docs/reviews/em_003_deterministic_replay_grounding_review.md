# EM-003 Deterministic Replay Grounding Review

## 1. Purpose

This review collects candidate grounding evidence for EM-003, specifically for deterministic and replayable requirements.

This document is evidence-collection only.

It does not:
- approve EM-003 as GROUNDED,
- change the active Evidence Matrix,
- change verifier expectations,
- grant implementation authority,
- authorize source-code changes,
- authorize test changes,
- authorize architecture refactoring.

The purpose is to preserve a fail-closed governance path while recording exact file and line references that may support a future, separate governance approval.

---

## 2. Current Governance State

Slice 1.0 remains blocked.

Authoritative governance state:

| Item | Current State | Evidence |
|------|---------------|----------|
| Slice status | BLOCKED | `slice_1_0_freeze_pack.md`, line 3 |
| Implementation authority | NONE | `slice_1_0_freeze_pack.md`, line 4 |
| Review scope | Documentation-only | `slice_1_0_governance_repair_review.md`, line 9 |
| Separate approval required | Yes | `slice_1_0_governance_repair_review.md`, line 40 |

No implementation authority is granted by this review.

---

## 3. EM-003 Current Matrix State

The current Evidence Matrix and verifier expectation are not aligned.

| Source | Location | Current / Expected Text | Meaning |
|--------|----------|--------------------------|---------|
| Evidence Matrix | `docs/freeze_packs/slice_1_0_evidence_matrix.md`, line 49 | `PARTIAL` with note that more specific references are needed | Matrix currently records partial evidence |
| Verifier | `scripts/verify_slice_1_0_governance_repair.ps1`, line 259 | `MISSING | Need exact file and line references showing deterministic/replayable requirements.` | Verifier expects fail-closed MISSING state |

Governance interpretation:

EM-003 must remain fail-closed until a separate explicit governance patch approves any status transition.

This review does not perform that transition.

---

## 4. Candidate Evidence Inventory

The following evidence items are collected as candidate grounding evidence for deterministic and replayable requirements.

They are not approval by themselves.

| Evidence ID | File | Lines | Evidence Summary | Supports | Review Note |
|-------------|------|-------|------------------|----------|-------------|
| EM003-EV-001 | `docs/core_contracts_principles.md` | 12 | Core contracts are required to be deterministic, replayable, serializable through a canonical policy, and independent from hidden wall-clock time. | Deterministic/replayable contract principles | Strong governance-level evidence |
| EM003-EV-002 | `docs/core_contracts_principles.md` | 13 | Structure-related contracts are also described as deterministic, replayable, canonical-policy serializable, and independent from hidden wall-clock time. | Deterministic/replayable structure contract expectations | Strong governance-level evidence |
| EM003-EV-003 | `docs/core_contracts_principles.md` | 14 | Canonical policy and hidden wall-clock independence are repeated as contract constraints. | Canonical serialization / time independence | Supports deterministic contract boundaries |
| EM003-EV-004 | `docs/core_contracts_principles.md` | 15 | Independence from wall-clock time is stated. | Replayability / deterministic evaluation | Directly supports replay safety |
| EM003-EV-005 | `docs/core_contracts_principles.md` | 16 | Canonical serialization and hidden wall-clock independence are restated. | Canonical serialization / deterministic behavior | Reinforces policy consistency |
| EM003-EV-006 | `docs/core_contracts_principles.md` | 17 | Canonical serialization and hidden wall-clock independence are restated. | Canonical serialization / deterministic behavior | Reinforces policy consistency |
| EM003-EV-007 | `docs/core_contracts_principles.md` | 21 | No Python contract implementation is frozen by this document; contract shape belongs to a later slice. | Governance boundary | Prevents accidental implementation authority |
| EM003-EV-008 | `docs/deterministic_assumptions_v1.md` | 8 | Candle order is ascending by canonical time. | Deterministic input ordering | Supports replayable ordering assumptions |
| EM003-EV-009 | `docs/deterministic_assumptions_v1.md` | 10 | Core logic does not inspect real wall-clock time during replay. | Replayability / deterministic evaluation | Direct replay constraint |
| EM003-EV-010 | `docs/deterministic_assumptions_v1.md` | 13 | Reporting language may vary, but deterministic truth may not. | Deterministic truth boundary | Prevents reporting-language ambiguity from changing truth |
| EM003-EV-011 | `docs/serialization_time_id_semantics_v1.md` | 11 | `created_at` participates in canonical serialization but does not participate in deterministic ID inputs. | Stable time/ID semantics | Important deterministic-ID distinction |
| EM003-EV-012 | `docs/serialization_time_id_semantics_v1.md` | 15 | Canonical serialization uses lexicographic ordering. | Canonical serialization stability | Supports stable canonical output |
| EM003-EV-013 | `src/smart_money/core/replay.py` | 7 | Replay module imports `deterministic_id`. | Replay implementation alignment | Candidate implementation evidence only |
| EM003-EV-014 | `src/smart_money/core/replay.py` | 8 | Replay module imports `ensure_utc_datetime`. | UTC-normalized replay/time handling | Candidate implementation evidence only |
| EM003-EV-015 | `src/smart_money/core/replay.py` | 40 | `ReplayManifest` class is defined. | Replay structure presence | Structural evidence, not approval evidence alone |
| EM003-EV-016 | `src/smart_money/core/replay.py` | 153 | Replay-related imports include deterministic ID, canonical JSON, and UTC time normalization aliases. | Deterministic ID / canonical serialization / UTC normalization | Candidate implementation evidence only |
| EM003-EV-017 | `tests/core/test_golden_replay.py` | 7 | Test exists for golden replay fixture slot usage. | Replay model shape stability | Test-level support |
| EM003-EV-018 | `tests/core/test_golden_replay.py` | 8 | Test checks absence of mutable instance dictionary or presence of `__slots__`. | Stable object shape | Test-level support |
| EM003-EV-019 | `tests/core/test_golden_replay.py` | 9 | Test checks `GoldenReplayFixture.__dataclass_params__.frozen is True`. | Immutability | Test-level support |
| EM003-EV-020 | `tests/core/test_golden_replay.py` | 10 | Test checks `GoldenReplayFixture` has `__slots__`. | Stable replay fixture structure | Test-level support |
| EM003-EV-021 | `tests/core/test_golden_replay.py` | 12 | Test exists for baseline replay pack slot usage. | Replay pack shape stability | Test-level support |
| EM003-EV-022 | `tests/core/test_golden_replay.py` | 13 | Test checks `BaselineReplayPack.__dataclass_params__.frozen is True`. | Immutability | Test-level support |
| EM003-EV-023 | `tests/core/test_golden_replay.py` | 14 | Test checks `BaselineReplayPack` has `__slots__`. | Stable replay pack structure | Test-level support |

---

## 5. Evidence Interpretation

The collected evidence indicates that the repository already contains multiple candidate references for deterministic and replayable behavior.

The strongest documentation-level references are:

1. `docs/core_contracts_principles.md`, lines 12-17  
   These lines describe deterministic, replayable, canonical-serialization, and wall-clock independence requirements.

2. `docs/deterministic_assumptions_v1.md`, lines 8, 10, and 13  
   These lines describe canonical candle ordering, no real wall-clock inspection during replay, and deterministic truth boundaries.

3. `docs/serialization_time_id_semantics_v1.md`, lines 11 and 15  
   These lines define the difference between canonical serialization and deterministic ID inputs, and specify lexicographic ordering for canonical serialization.

The strongest code/test-level references are:

1. `src/smart_money/core/replay.py`, lines 7, 8, 40, and 153  
   These lines show replay-related usage of deterministic IDs, UTC datetime normalization, canonical JSON, and the `ReplayManifest` structure.

2. `tests/core/test_golden_replay.py`, lines 7-14  
   These lines verify frozen dataclass behavior and slot-based replay fixture/pack structure.

However, code/test evidence must be interpreted carefully because this review does not authorize implementation changes and does not grant authority to expand Slice 1.0.

---

## 6. Gap Analysis

The repository contains credible candidate evidence for EM-003.

However, EM-003 must remain fail-closed because:

1. The active Evidence Matrix currently records EM-003 as `PARTIAL`.
2. The verifier expects EM-003 to be `MISSING` with exact file and line references.
3. This review only collects candidate evidence.
4. No separate governance patch has approved EM-003 status transition.
5. Slice 1.0 remains `BLOCKED`.
6. Implementation Authority remains `NONE`.
7. Existing governance review language requires a separate and explicit approval before implementation authority can be granted.

Therefore, this review is not sufficient to mark EM-003 as GROUNDED.

A future governance patch may use this evidence, but that patch must be explicit, narrow, deterministic, replayable, and documentation-only unless a later Freeze Pack grants broader authority.

---

## 7. Review Decision

Decision: NOT APPROVED FOR STATUS CHANGE

EM-003 remains fail-closed.

This review does not approve:
- `GROUNDED` status,
- `APPROVED` status,
- implementation authority,
- verifier changes,
- source-code changes,
- test changes,
- package restructuring,
- architecture refactoring.

This review only records candidate grounding evidence.

---

## 8. Required Future Governance Step

To transition EM-003 from fail-closed state to a grounded state, a separate governance patch is required.

That future patch must explicitly state:

1. the intended EM-003 target status,
2. the exact Evidence Matrix row change,
3. whether verifier expectations must change,
4. the exact file and line references being accepted,
5. that Slice 1.0 implementation authority remains unchanged unless separately approved,
6. that no source-code or test change is included unless a Freeze Pack explicitly grants that scope.

Until that future patch exists and is approved, EM-003 remains not approved for status change.

---

## 9. Final Governance Statement

This document is documentation-only.

It collects deterministic and replayable evidence for future review.

It does not change project authority.

It does not change active Slice scope.

It does not change the verifier.

It does not change implementation status.

It does not override the fail-closed governance model.
