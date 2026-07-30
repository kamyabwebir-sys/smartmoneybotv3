\# Slice 1.7 — EM-003 Verifier Evidence Report Shape Lock



Status: PROPOSED  

Implementation Authority: NONE  

Approval Status: NOT APPROVED  

Scope: Governance / Evidence / Documentation Only  

EM-003 Status: PARTIAL  



\---



\## 1. Purpose



Slice 1.7 locks the expected evidence report shape for future EM-003 replayability verifiers.



This slice does not implement a verifier, test, script, schema validator, runtime reporter, replay engine, serializer, registry change, or domain model change.



The purpose is to define the minimum deterministic evidence artifact shape that future verifier work must produce before EM-003 can be considered for promotion.



\---



\## 2. Governance Position



This slice is governance-only.



It grants no implementation authority.



It does not approve changes in:



\- `src/`

\- `tests/`

\- `scripts/`

\- runtime code

\- replay engines

\- canonical serializer code

\- registry code

\- reporting/UI code

\- adapters

\- execution logic

\- risk logic

\- ML decisioning logic



Any future implementation must be introduced through a separate Freeze Pack.



\---



\## 3. Relationship to Previous Slices



This slice depends on the governance intent of:



\- Slice 1.4 — EM-003 replayability grounding and verifier design

\- Slice 1.5 — EM-003 acceptance criteria lock

\- Slice 1.6 — EM-003 verifier case matrix lock



Slice 1.7 does not replace those slices.



It only defines the future evidence report shape required to connect:

```text

Acceptance Criteria -> Verifier Case -> Evidence Result -> Governance Review



\---



\## 4. EM-003 Status



EM-003 remains:



text

PARTIAL



This slice does not promote EM-003 to GROUNDED.



Promotion is only allowed after future verifier evidence exists, is complete, is deterministic, and is reviewed under a separate approval slice.



\---



\## 5. Future Evidence Report Shape



A future EM-003 verifier evidence report must contain the following top-level sections.



This is a documentation lock only. No schema or validator is implemented in this slice.



text

report\_id

report\_version

slice\_reference

em\_id

generated\_by

generated\_at\_policy

input\_identity

environment\_policy

case\_results

summary

fail\_closed\_verdict

traceability

review\_notes



\---



\## 6. Required Top-Level Fields



\### 6.1. `report\_id`



A stable identifier for the evidence report.



Future rule:



text

report\_id must be deterministic or explicitly derived from canonical input identity.



Fail-closed if:



\- report\_id is missing

\- report\_id is random

\- report\_id depends on wall-clock time

\- report\_id cannot be traced to input identity



\---



\### 6.2. `report\_version`



The version of the evidence report shape.



Initial locked value for future implementation:



text

em003-evidence-report-v1



Fail-closed if:



\- report\_version is missing

\- report\_version is unknown

\- report\_version is ambiguous

\- report\_version is not supported by the reviewing slice



\---



\### 6.3. `slice\_reference`



The slice or freeze pack that authorized the verifier implementation.



Required future fields:



text

slice\_id

freeze\_pack\_path

commit\_id

approval\_status

implementation\_authority



Fail-closed if:



\- slice\_id is missing

\- freeze\_pack\_path is missing

\- commit\_id is missing

\- approval\_status is not explicit

\- implementation\_authority is not explicit



\---



\### 6.4. `em\_id`



The evidence matrix identifier.



Required locked value:



text

EM-003



Fail-closed if:



\- em\_id is missing

\- em\_id is not EM-003

\- multiple EM IDs are mixed in the same report without explicit approval



\---



\### 6.5. `generated\_by`



The verifier identity.



Required future fields:



text

verifier\_name

verifier\_version

verifier\_mode



Allowed future verifier mode:



text

deterministic-read-only



Fail-closed if:



\- verifier identity is missing

\- verifier version is missing

\- verifier mode is not read-only

\- verifier mode implies mutation or runtime execution authority



\---



\### 6.6. `generated\_at\_policy`



Wall-clock timestamps must not influence replay results.



Allowed future timestamp posture:



text

timestamp may exist as metadata only

timestamp must not affect case results

timestamp must not affect canonical output identity

timestamp must not affect verdict



Fail-closed if:



\- timestamp affects result

\- timestamp affects report\_id

\- timestamp affects canonical replay output

\- timezone or locale changes verdict



\---



\### 6.7. `input\_identity`



The evidence report must identify the inputs used by the verifier.



Required future fields:



text

fixture\_id

fixture\_path

fixture\_content\_hash

canonical\_input\_hash

input\_contract\_version



Fail-closed if:



\- fixture identity is missing

\- fixture path is ambiguous

\- fixture hash is missing

\- canonical input hash is missing

\- input contract version is missing

\- input cannot be reproduced



\---



\### 6.8. `environment\_policy`



The report must state the environment assumptions without allowing environment-specific variance to pass.



Required future fields:



text

os\_policy

locale\_policy

timezone\_policy

filesystem\_order\_policy

randomness\_policy

clock\_policy



Required locked posture:



text

environment must not change verifier verdict



Fail-closed if:



\- locale changes output

\- timezone changes output

\- filesystem order changes output

\- hostname changes output

\- machine-specific path changes output

\- randomness affects output

\- current clock affects output



\---



\### 6.9. `case\_results`



The report must include one result per required case from the locked case matrix.



Each case result must include:



text

case\_id

acceptance\_area

input\_fixture\_identity

expected\_output\_identity

actual\_output\_identity

status

failure\_reason

linked\_acceptance\_criterion

linked\_evidence\_reference



Allowed future statuses:



text

PASS

FAIL



Not allowed as passing statuses:



text

SKIPPED

UNKNOWN

PARTIAL

INCONCLUSIVE

NOT\_RUN



Fail-closed if:



\- case\_id is missing

\- case\_id is unknown

\- case is skipped

\- case is partial

\- expected output is missing

\- actual output is missing

\- linked acceptance criterion is missing

\- linked evidence reference is missing

\- failure reason is missing for failed cases



\---



\### 6.10. `summary`



The report summary must be mechanically derivable from case results.



Required future fields:



text

total\_cases

passed\_cases

failed\_cases

skipped\_cases

unknown\_cases

overall\_status



Required future rule:



text

overall\_status may be PASS only if every required case is PASS.



Fail-closed if:



\- summary counts do not match case\_results

\- any required case is missing

\- any case is skipped

\- any case is unknown

\- any case is partial

\- summary says PASS while any case is not PASS



\---



\### 6.11. `fail\_closed\_verdict`



The report must include an explicit fail-closed verdict.



Allowed future values:



text

PASS

FAIL



Required future rule:



text

Any ambiguity must result in FAIL.



Fail-closed if:



\- verdict is missing

\- verdict is not PASS or FAIL

\- verdict is manually overridden without evidence

\- verdict conflicts with case\_results

\- verdict conflicts with summary



\---



\### 6.12. `traceability`



The report must map each verifier case back to locked governance material.



Required future traceability fields:



text

case\_id

acceptance\_criterion\_id

freeze\_pack\_reference

evidence\_matrix\_id

source\_slice



Fail-closed if:



\- traceability is missing

\- case has no acceptance criterion mapping

\- case has no freeze pack reference

\- case has no EM-003 mapping

\- source slice is ambiguous



\---



\### 6.13. `review\_notes`



Review notes are allowed, but they must not affect the mechanical verdict.



Required future posture:



text

review\_notes are descriptive only

review\_notes cannot convert FAIL to PASS

review\_notes cannot promote EM-003



Fail-closed if:



\- review notes override verifier results

\- review notes promote EM-003 without separate approval

\- review notes conflict with case\_results



\---



\## 7. Minimum Required Case Coverage



A future report must include at least the case IDs locked by Slice 1.6:



text

EM003-CASE-001

EM003-CASE-002

EM003-CASE-003

EM003-CASE-004

EM003-CASE-005

EM003-CASE-006

EM003-CASE-007

EM003-CASE-008

EM003-CASE-009

EM003-CASE-010



Fail-closed if any required case is absent.



\---



\## 8. Non-Goals



This slice does not define or implement:



\- JSON schema files

\- pytest tests

\- verifier CLI

\- replay fixtures

\- golden files

\- runtime report generation

\- dashboard reports

\- Telegram reports

\- analytics scoring

\- trading decisions

\- risk decisions

\- ML decisions



\---



\## 9. Protected Paths



This slice permits changes only under:



text

docs/freeze\_packs/



This slice does not permit changes under:



text

src/

tests/

scripts/



\---



\## 10. Future Implementation Gate



Before any future verifier implementation is allowed, a separate Freeze Pack must explicitly approve:



text

implementation authority

allowed paths

test scope

fixture scope

report artifact format

failure behavior

review process



Until then, this document remains a governance-only lock.



\---



\## 11. Expected Slice Verdict



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

\- Implementation Authority remains NONE

\- Approval Status remains NOT APPROVED

