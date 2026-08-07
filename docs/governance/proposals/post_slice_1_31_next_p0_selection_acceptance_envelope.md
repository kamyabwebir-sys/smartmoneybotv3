# Post-Slice 1.31 Next P0 Selection Acceptance Envelope

Status: Proposal-Only
Scope: Governance-Only
Lane: Fast Lane
Parent Slice: slice_1_31
Decision Class: Post-1.31 P0 Candidate Selection
Mutation Policy: No protected-file mutation
Execution Policy: No execution logic
Risk Policy: No risk calculation
ML Policy: No opaque ML decisioning

## 1. Purpose

This document defines the acceptance envelope for selecting the next P0 governance-approved implementation target after slice 1.31.

The goal is to select the narrowest viable next unit of work that:

- preserves determinism,
- preserves replayability,
- avoids protected-file mutation,
- remains governance-first,
- creates reusable contract spine for later analytics work,
- does not introduce execution, trading, or direct decisioning behavior.

This document does not authorize implementation by itself.
This document only authorizes candidate ranking, scope narrowing, and governance alignment.

## 2. Governance Basis

This proposal is grounded in the following existing governance rules:

- Slice 1.31 operating budget limits governance slices to a narrow file budget.
- Slice 1.31 defines Fast Lane for patch/verifier/evidence/canonicalization work.
- Slice 1.31 failure taxonomy includes:
  - CANONICAL_HASH_DRIFT
  - PROTECTED_FILE_MUTATION
  - EVIDENCE_GROUNDING_GAP
- Slice 1.31 guardrails prohibit:
  - execution logic
  - risk calculation
  - ML decisioning in Core/Domain

## 3. Problem Statement

Post-1.31, the repository has governance momentum and read-only consumption discipline around discovery-related evidence work, but it does not yet have a formally accepted post-1.31 P0 selection envelope for the next narrow, deterministic, replayable foundation contract slice.

Without an explicit acceptance envelope:

- next-scope selection may drift,
- architecture intent may be over-interpreted into premature refactor,
- analytics candidate work may leak into decisioning,
- protected slices may become indirect refactor pressure points,
- replayability and evidence grounding may become under-specified.

## 4. Scope of This Proposal

This proposal is limited to:

- defining candidate set,
- defining evaluation rubric,
- defining explicit acceptance and rejection criteria,
- selecting one recommended P0 candidate set,
- documenting non-goals,
- documenting protected boundaries,
- documenting what future implementation must preserve.

This proposal does not:

- create runtime code,
- create domain models,
- create adapters,
- create reporting outputs,
- modify registry behavior,
- modify replay behavior,
- change evidence semantics.

## 5. Protected Boundaries

The following files are protected and must not be changed by the implementation slice derived from this proposal unless explicitly re-authorized by a dedicated slice:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

The selection made here must prefer candidates that do not require touching protected files.

## 6. Candidate Set

The following candidates are admitted into the evaluation set.

### 6.1 Candidate A — `AnalysisRequest`

A narrow request contract describing a deterministic analysis invocation boundary.

Expected role:
- identifies the request intent,
- references canonical input scope,
- does not carry execution intent,
- does not embed trading action semantics,
- supports deterministic serialization and replay traceability.

Expected value:
- establishes a stable application/domain-facing request seam,
- improves later analytics composition,
- remains neutral to reporting and adapters.

### 6.2 Candidate B — `InputBundleManifest`

A canonical manifest contract describing what immutable inputs participated in a replayable analysis unit.

Expected role:
- enumerates input artifacts,
- records canonical identity references,
- supports reproducibility and replay inspection,
- provides evidence-chain entry points.

Expected value:
- strengthens replayability and evidence grounding,
- is read-only and deterministic by construction,
- can remain independent from execution concerns.

### 6.3 Candidate C — `RegimeFeatureVector`

A deterministic feature-shape contract for historical evidence comparison.

Expected role:
- represents explicit, explainable, non-opaque features,
- supports future analytics evidence retrieval,
- must remain non-decisioning and non-executing.

Expected risk:
- may trigger premature debates about feature semantics,
- may imply downstream scoring before request/manifest spine is locked.

### 6.4 Candidate D — `WeightedRegimeSimilarity`

A deterministic score-breakdown contract for similarity evaluation between current evidence and historical evidence buckets.

Expected role:
- expose score breakdown only,
- expose evidence references only,
- produce no verdict or action.

Expected risk:
- more likely than upstream contracts to be misread as decisioning,
- depends on prior stabilization of request/input/evidence contracts.

### 6.5 Candidate E — `MarketMetricBreakdown`

A breakdown contract for observable market metrics.

Expected role:
- explain metric components,
- remain evidence-oriented,
- avoid outcome recommendation.

Expected risk:
- broader semantic surface area,
- greater chance of reporting leakage into domain concerns.

### 6.6 Candidate F — `MarketInstabilityEvidence`

A contract for evidence-only representation of instability conditions.

Expected role:
- package instability evidence,
- remain descriptive rather than prescriptive,
- anchor future score breakdowns.

Expected risk:
- terminology may invite risk semantics if introduced too early,
- should follow rather than precede request/input spine.

## 7. Evaluation Rubric

Each candidate shall be evaluated using the already approved post-1.31 prioritization model:

PriorityScore = (4 * UnlockValue) + (3 * DeterminismRisk) + (2 * ScopeSafety) + (1 * LowCost)

Interpretation for this proposal:

- **UnlockValue**
  How much future deterministic analytics work becomes easier if this contract is locked first.

- **DeterminismRisk**
  How strongly the candidate helps reduce ambiguity or drift in future deterministic and replayable behavior.

- **ScopeSafety**
  How safely the candidate stays within governance boundaries and avoids leakage into execution/risk/reporting.

- **LowCost**
  How likely the candidate can be introduced in a narrow slice without protected-file mutation or broad refactor.

## 8. Candidate Assessment

### 8.1 `AnalysisRequest`

#### Strengths
- narrow contract surface,
- strong architectural unlock value,
- low likelihood of reporting leakage,
- clear separation from execution logic,
- suitable as a neutral application/domain seam.

#### Risks
- if over-designed, could prematurely encode orchestration concerns.

#### Assessment
- high unlock value,
- high scope safety,
- medium-to-high determinism support,
- low implementation cost.

### 8.2 `InputBundleManifest`

#### Strengths
- directly reinforces replayability,
- directly reinforces evidence grounding,
- naturally read-only,
- naturally compatible with canonical serialization.

#### Risks
- if over-expanded, could become an artifact registry substitute.

#### Assessment
- high determinism support,
- high scope safety,
- high replayability value,
- low implementation cost.

### 8.3 `RegimeFeatureVector`

#### Strengths
- useful for future historical evidence retrieval,
- explicit feature representation is preferable to opaque inference.

#### Risks
- can trigger premature domain debate,
- may be too early before request/input contracts are formalized.

#### Assessment
- medium unlock value now,
- medium scope safety now,
- not the safest first post-1.31 P0.

### 8.4 `WeightedRegimeSimilarity`

#### Strengths
- aligns with evidence + score breakdown model,
- useful later for analytics explanation.

#### Risks
- too easy to misread as decision output,
- depends on prior contract spine,
- raises semantics earlier than necessary.

#### Assessment
- valuable later,
- not optimal as immediate P0.

### 8.5 `MarketMetricBreakdown`

#### Strengths
- explainability-friendly,
- evidence-compatible if kept descriptive.

#### Risks
- broader than necessary for the next narrow slice,
- may leak presentation/reporting semantics.

#### Assessment
- useful candidate, but not first.

### 8.6 `MarketInstabilityEvidence`

#### Strengths
- evidence-oriented framing is compatible with guardrails.

#### Risks
- “instability” may create premature risk interpretation pressure,
- better introduced after request/input grounding.

#### Assessment
- acceptable future candidate,
- not ideal first P0.

## 9. Selection Decision

### Recommended P0 Selection

The recommended post-slice-1.31 P0 direction is:

1. `AnalysisRequest`
2. `InputBundleManifest`

### Selection Rationale

This is a paired foundation spine selection, not a broad feature expansion.

The pair is selected because:

- `AnalysisRequest` defines the deterministic request boundary,
- `InputBundleManifest` defines the replayable input boundary,
- together they create a stable contract spine for future analytics evidence work,
- neither requires direct mutation of discovery registry behavior,
- neither implies execution or decisioning,
- both support later evidence-chain grounding,
- both are narrower and safer than similarity or regime-scoring constructs.

## 10. Acceptance Criteria for the Future Implementation Slice

A future implementation slice derived from this envelope is acceptable only if all conditions below remain true:

1. No protected-file mutation:
   - `src/smart_money/discovery/registry.py`
   - `tests/discovery/test_registry.py`

2. No execution/trading logic introduced.

3. No risk calculation introduced.

4. No opaque ML decisioning introduced.

5. No reporting/UI leakage into core/domain contracts.

6. Contracts remain deterministic and replayable.

7. Contracts remain immutable in spirit and canonically serializable.

8. Any scoring-related concept is deferred unless represented strictly as evidence breakdown without verdict.

9. File budget remains narrow and explicitly justified.

10. A verifier must fail closed if the proposal document is missing required governance sections.

## 11. Rejection Criteria

A future implementation proposal shall be rejected if any of the following becomes true:

- it requires registry mutation,
- it introduces runtime execution behavior,
- it embeds action recommendation,
- it introduces non-canonical serialization ambiguity,
- it mixes reporting semantics into domain/core contracts,
- it expands beyond narrow contract introduction into broad refactor,
- it turns evidence contracts into direct decision outputs.

## 12. Non-Goals

The following are explicitly out of scope for the next P0 implementation slice:

- trade execution
- order routing
- position sizing
- risk scoring as decision logic
- ML-driven inference
- alert verdict generation
- reporting templates
- dashboard output structures
- adapter/provider implementation
- registry redesign
- replay engine redesign

## 13. Future Work Queue

The following remain valid future candidates after the foundation spine is accepted:

- `RegimeFeatureVector`
- `WeightedRegimeSimilarity`
- `MarketMetricBreakdown`
- `MarketInstabilityEvidence`

Suggested ordering after foundation spine:

1. `RegimeFeatureVector`
2. `MarketMetricBreakdown`
3. `MarketInstabilityEvidence`
4. `WeightedRegimeSimilarity`

This ordering is preferred because it keeps semantics explicit before similarity scoring is introduced.

## 14. Governance Verdict

Verdict: Accepted as proposal envelope for post-slice-1.31 P0 selection.

Meaning of verdict:
- candidate narrowing is approved,
- implementation is not yet approved,
- a dedicated future slice is still required for any code or contract introduction.

## 15. Implementation Handoff Note

If a future slice implements the selected P0 pair, it should remain minimal and preferably target contract introduction only.

Preferred implementation characteristics:
- narrow file count,
- deterministic serialization compatibility,
- replayability-first naming,
- no adapter or reporting coupling,
- verifier-backed fail-closed governance checks.

## 16. Final Constraint Summary

This proposal is valid only while all of the following remain true:

- governance-first posture is preserved,
- protected files remain untouched,
- determinism is not weakened,
- replayability is strengthened or preserved,
- evidence remains descriptive rather than prescriptive,
- architecture target is used as direction, not as automatic refactor authority.