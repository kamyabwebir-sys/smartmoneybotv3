# Separate Approval Review Template

Project: SmartMoneyBotV3  
Review Type: Explicit Governance Approval Review  
Purpose: Determine whether the current BLOCKED state can transition to a narrowly authorized next stage

---

## 1. Governance Position

This template is a review artifact only.  
It does **not** by itself authorize:

- source mutation
- test mutation
- package creation
- package rename
- module move
- broad refactor
- architecture migration

Any progression authorization is valid only if a reviewer explicitly selects the progression option and fully completes all required fields.

---

## 2. Current Authoritative Baseline

Reviewer must confirm the current baseline before any decision:

- Current Slice:
- Current Slice Status:
- Current Implementation Authority:
- Current EM-003 Status:

Baseline references:

- Freeze Pack file + line references:
- Evidence Matrix file + line references:
- Governance Review file + line references:
- Verifier file + line references:

Reviewer confirmation:

- [ ] I confirm the baseline state is accurately grounded
- [ ] I confirm verifier PASS is preservation-only, not progression authority

---

## 3. Decision Mode

Choose exactly one:

- [ ] OPTION A — Remain BLOCKED
- [ ] OPTION B — Review-Sufficient Only, No Progression
- [ ] OPTION C — Explicit Progression Approval

Rules:

1. If OPTION A or OPTION B is selected, OPTION C fields must remain empty.
2. If OPTION C is selected, **all required fields must be completed**.
3. Any omitted OPTION C field invalidates the approval.
4. Ambiguous language is non-authorizing by default.

---

## 4. OPTION A — Remain BLOCKED

Complete this section only if OPTION A is selected.

### 4.1 State Preservation

- Slice Status remains:
- Implementation Authority remains:
- EM-003 remains:

### 4.2 Exact Blockers

- Blocker 1:
- Blocker 2:
- Blocker 3:

### 4.3 Minimum Requirements to Unblock

- Requirement 1:
- Requirement 2:
- Requirement 3:

---

## 5. OPTION B — Review-Sufficient Only, No Progression

Complete this section only if OPTION B is selected.

### 5.1 Review Sufficiency

- Evidence sufficient for review because:

### 5.2 Explicit Non-Authorization

- No implementation is authorized:
- No progression is authorized:
- No src/ mutation is authorized:
- No tests/ mutation is authorized:

### 5.3 Remaining Blocker

- Remaining blocker:

### 5.4 Separate Approval Still Required

- Exact approval still required:

---

## 6. OPTION C — Explicit Progression Approval

Complete this section only if OPTION C is selected.

**Hard rule:** every field below is required.  
If any field is blank, the approval is invalid.

### 6.1 Approval Type

- Approval Type:
- This review explicitly serves as the separate approval review required by governance:
  - [ ] YES
  - [ ] NO

### 6.2 State Transition

- Previous Slice Status:
- New Slice Status:
- Previous Implementation Authority:
- New Implementation Authority:

### 6.3 EM-003 Disposition

- Previous EM-003 Status:
- New EM-003 Status:

Exact evidence references:

- File:
- Line(s):
- Deterministic requirement grounded by this reference:
- Replayable requirement grounded by this reference:

Reviewer justification:

- Why EM-003 is sufficiently grounded for this transition:

### 6.4 Authorized Scope

- Allowed files:
- Allowed directories:
- Allowed tests:
- Allowed documentation files:
- src/ changes allowed:
- tests/ changes allowed:
- docs-only changes allowed:
- new files allowed:
- package/module moves allowed:

### 6.5 Forbidden Scope

The following remain forbidden unless separately authorized:

- execution/trading logic
- risk calculation
- opaque ML decisioning
- reporting/UI leakage into core/domain
- broad refactor
- package rename
- module move
- future architecture folder scaffolding without Freeze Pack authority

Reviewer confirmation:

- [ ] confirmed

### 6.6 Next Stage Boundary

- Next authorized slice or stage:
- Purpose:
- Exact in-scope files:
- Exact out-of-scope files:
- Required tests:
- Verification command or review requirement:
- Acceptance criteria:
- Stop condition:

### 6.7 Verification Alignment

- Existing verifier relevance:
- Additional verification required:
- Any required verifier/document update:
- Why this remains deterministic and replayable:

### 6.8 Final Authorization Sentence

Required exact-style sentence:

I explicitly authorize progression from [previous state] to [new state] under the boundaries listed above. This authorization is limited to [exact scope] and does not authorize any out-of-scope mutation.

---

## 7. Ambiguity Rule

The following phrases are non-authorizing unless fully expanded into OPTION C fields:

- LGTM
- looks good
- sufficient
- approved generally
- continue
- proceed

Default interpretation under ambiguity:

- Current BLOCKED state is preserved

---

## 8. Reviewer Signature

- Name:
- Role:
- Date:
- Final Decision:
- Signature / explicit approval text:
