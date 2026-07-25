\# Slice 1.6 — EM-003 Replayability Verifier Case Matrix Lock



Status: PROPOSED  

Implementation Authority: NONE  

Approval Status: NOT APPROVED  

Scope: Governance / Evidence / Documentation Only  

EM-003 Status: PARTIAL  



\---



\## 1. Purpose



Slice 1.6 locks the future verifier case matrix for EM-003 replayability validation.



This slice does not implement any verifier, test, runtime behavior, replay engine, serializer, registry change, or domain model change.



The only purpose is to define a deterministic and fail-closed mapping between the Slice 1.5 acceptance criteria and future verifier cases.



\---



\## 2. Governance Position



This slice is governance-only.



It grants no implementation authority.



It does not approve changes in:



\- `src/`

\- `tests/`

\- runtime code

\- replay engines

\- serializer code

\- registry code

\- reporting code

\- execution logic

\- risk logic

\- ML decisioning logic



Any future implementation must be introduced through a separate Freeze Pack.



\---



\## 3. EM-003 Status



EM-003 remains:

```text

PARTIAL



This slice does not promote EM-003 to GROUNDED.



Promotion is only allowed after future verifier evidence exists and is reviewed under a separate approval slice.



\---



\## 4. Future Verifier Case Matrix



The following matrix defines the minimum future verification cases required before EM-003 can be considered for promotion.



| Case ID | Acceptance Area | Future Verifier Intent | Expected Fail-Closed Behavior | Implementation Now |

|---|---|---|---|---|

| EM003-CASE-001 | Canonical serialization stability | Same input produces byte-stable or text-stable canonical output | Fail if serialization output differs across repeated runs | NONE |

| EM003-CASE-002 | Deterministic ordering | Equivalent unordered inputs normalize into a stable deterministic order | Fail if output order depends on insertion order, filesystem order, or runtime iteration variance | NONE |

| EM003-CASE-003 | No wall-clock dependency | Replay result must not depend on current system time | Fail if `now`, local timezone, or runtime clock changes output | NONE |

| EM003-CASE-004 | No randomness dependency | Replay result must not depend on random state | Fail if unseeded randomness or entropy affects output | NONE |

| EM003-CASE-005 | Stable identifiers | IDs must be deterministic from canonical input material | Fail if identifiers change between equivalent replays | NONE |

| EM003-CASE-006 | Stable error surface | Invalid replay input must fail with stable error categories and reason codes | Fail if errors are opaque, unstable, or environment-dependent | NONE |

| EM003-CASE-007 | Manifest completeness | Replay artifact must declare sufficient deterministic assumptions and input identity | Fail if required manifest fields are missing or ambiguous | NONE |

| EM003-CASE-008 | Environment isolation | Replay result must not depend on machine-specific paths, locale, hostnames, or OS-specific ordering | Fail if environment variance changes output | NONE |

| EM003-CASE-009 | Golden replay consistency | A known input fixture must produce the same canonical replay evidence across runs | Fail if golden output drifts without explicit approved contract change | NONE |

| EM003-CASE-010 | Evidence traceability | Verifier output must map results back to acceptance criteria and evidence IDs | Fail if result cannot be traced to locked criteria | NONE |



\---



\## 5. Required Future Evidence



A future implementation slice must provide evidence for each case ID.



Minimum future evidence shape:



text

Case ID

Input fixture identity

Canonical output identity

Expected result

Actual result

Pass/fail status

Failure reason if any

Linked acceptance criterion

Linked evidence reference



This slice does not create that evidence.



\---



\## 6. Fail-Closed Rules



Future verifier behavior must be fail-closed.



The verifier must fail if:



\- expected fixture is missing

\- canonical output cannot be produced

\- environment-dependent value is detected

\- replay output differs from locked expectation

\- evidence reference is missing

\- acceptance criterion mapping is incomplete

\- case ID is unknown

\- result is ambiguous

\- verifier cannot determine status deterministically



No unknown, skipped, ambiguous, or partial case may be treated as pass.



\---



\## 7. Protected Paths



This slice permits changes only under:



text

docs/freeze\_packs/



This slice does not permit changes under:



text

src/

tests/

scripts/



\---



\## 8. Approval Boundary



This document is not an implementation approval.



It only locks the future verifier case matrix.



A separate Freeze Pack is required before any verifier, test, script, or runtime code may be created.



\---



\## 9. Slice Verdict



Expected verdict if only this document is added:



text

PASS / GOVERNANCE-ONLY / FAIL-CLOSED-COMPLIANT



Required checks:



text

git status --short

git show --name-status --oneline HEAD

git show --name-only --format= HEAD | Select-String "^(src/|tests/|scripts/)"



Acceptance condition:



\- working tree clean after commit

\- only this document added

\- no protected path changes

\- EM-003 remains PARTIAL

