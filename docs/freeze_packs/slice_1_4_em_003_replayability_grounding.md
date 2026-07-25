# Slice 1.4 — EM-003 Direct Replayability Grounding

Status: PROPOSED  
Implementation Authority: NONE  
Approval Status: NOT APPROVED  
Classification: Governance / Evidence / Documentation Only

---

## 1. Purpose

This Freeze Pack proposes a narrow governance-only path for grounding review of EM-003:

`Deterministic / Replayable grounding`

The purpose of this slice is to define:

- the replayability review target,
- the canonical baseline,
- replay scenarios,
- independent verifier constraints,
- evidence capture requirements,
- acceptance criteria,
- fail-closed interpretation rules.

This slice does not approve implementation work.

This slice does not modify runtime behavior.

This slice does not modify test behavior.

This slice does not promote EM-003 status.

EM-003 remains `PARTIAL` unless and until separate explicit governance acceptance confirms sufficient evidence.

---

## 2. Authority Boundary

This Freeze Pack is documentation-only.

Allowed paths:

- `docs/freeze_packs/*.md`
- `docs/reviews/*.md`

Disallowed paths:

- `src/`
- `tests/`
- `scripts/`
- `tools/`
- runtime configuration files
- package/module layout files

This Freeze Pack grants no authority to:

- change source code,
- change tests,
- add committed verifier scripts,
- alter runtime behavior,
- alter test behavior,
- rename packages,
- move modules,
- introduce architecture folders,
- introduce trading/execution logic,
- introduce risk calculation,
- introduce ML decisioning,
- introduce reporting/UI behavior into core/domain logic.

---

## 3. Current EM-003 Posture

Current status:

`EM-003: PARTIAL`

This status must remain unchanged during this slice.

This slice only defines the governance path and evidence shape needed for future review.

No document produced under this slice may claim:

- approval,
- closure,
- evidence sufficiency,
- implementation authority,
- governance completion,
- EM-003 status promotion.

Any future status change requires a separate explicit governance decision.

---

## 4. Authoritative Existing Files

The following files are authoritative for this slice:

- `docs/freeze_packs/slice_1_0_freeze_pack.md`
- `docs/freeze_packs/slice_1_0_evidence_matrix.md`
- `docs/freeze_packs/slice_1_2_freeze_pack_replacement_audit_checklist.md`
- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

The current source and test files are review references only.

They are not authorized for modification by this slice.

---

## 5. Review Target

The only runtime behavior under review is:

`DiscoveryRegistry.list_ids()`

The relevant existing behavior is that `list_ids()` returns a sorted tuple of registered discovery IDs.

The review target is narrow:

Given the same discovery ID set, different registration orders must produce the same canonical sorted tuple.

---

## 6. Replayability Baseline

The baseline discovery ID set is exactly:

- `zeta.discovery`
- `alpha.discovery`
- `middle.discovery`

The expected canonical output is exactly:

```python
("alpha.discovery", "middle.discovery", "zeta.discovery")

The baseline is order-independent.

Any deviation from the expected canonical output is a fail-closed result.

---

## 7. Replay Scenarios

### Scenario A

Registration order:

1. `zeta.discovery`
2. `alpha.discovery`
3. `middle.discovery`

Expected output:

python
("alpha.discovery", "middle.discovery", "zeta.discovery")

### Scenario B

Registration order:

1. `middle.discovery`
2. `zeta.discovery`
3. `alpha.discovery`

Expected output:

python
("alpha.discovery", "middle.discovery", "zeta.discovery")

### Scenario C

Registration order:

1. `alpha.discovery`
2. `middle.discovery`
3. `zeta.discovery`

Expected output:

python
("alpha.discovery", "middle.discovery", "zeta.discovery")

---

## 8. Independent Verifier Constraints

Any verifier used to collect future evidence must be independent and local-only unless a later Freeze Pack explicitly authorizes committed verifier artifacts.

The verifier must:

- conform to the existing `StructureDiscovery` protocol,
- provide a `discovery_id` property,
- provide a `discover(context)` method,
- register the same discovery ID set in each scenario,
- compare `DiscoveryRegistry.list_ids()` output with the canonical baseline,
- record observed output for each scenario,
- fail closed on mismatch,
- fail closed on exception,
- fail closed on missing evidence,
- fail closed on ambiguous output.

The verifier must not:

- modify `src/`,
- modify `tests/`,
- patch `DiscoveryRegistry`,
- patch `StructureDiscovery`,
- depend on wall-clock time,
- depend on randomness,
- depend on external services,
- depend on network access,
- perform trading/execution behavior,
- perform risk calculation,
- perform ML decisioning,
- emit reporting/UI behavior into core/domain logic.

---

## 9. Known Non-Conformance Interpretation

A previous verifier attempt failed with:

text
AttributeError: 'ReplayObject' object has no attribute 'discovery_id'

This must be interpreted as verifier non-conformance.

It must not be interpreted as a source-code defect.

The accepted remedy is not to modify `src/` or `tests`.

The accepted remedy is to design any future verifier object so that it conforms to the existing `StructureDiscovery` protocol.

---

## 10. Evidence Capture Requirements

Future evidence must capture:

- repository commit hash,
- branch name,
- operating system,
- Python version,
- command invocation, if any,
- exact baseline,
- exact scenario registration order,
- observed output per scenario,
- expected output per scenario,
- pass/fail result per scenario,
- exception trace if any,
- confirmation that no `src/` file was modified,
- confirmation that no `tests/` file was modified,
- confirmation that no committed verifier script was added unless separately authorized.

Evidence must be plain-text or markdown.

Evidence must be deterministic and replayable.

Evidence must be sufficient for independent review.

If evidence is incomplete, ambiguous, environment-dependent, or non-replayable, the result must remain fail-closed.

---

## 11. Acceptance Criteria

This slice is acceptable only if it remains documentation-only and defines a clear governance path for future EM-003 review.

Acceptance criteria for this slice:

- [ ] Only documentation paths are proposed.
- [ ] No `src/` change is authorized.
- [ ] No `tests/` change is authorized.
- [ ] No committed verifier script is authorized.
- [ ] `Implementation Authority` remains `NONE`.
- [ ] `Approval Status` remains `NOT APPROVED`.
- [ ] EM-003 remains `PARTIAL`.
- [ ] The replayability baseline is explicitly defined.
- [ ] Replay scenarios A, B, and C are explicitly defined.
- [ ] Expected canonical output is explicitly defined.
- [ ] Verifier constraints are fail-closed.
- [ ] Known verifier non-conformance is interpreted as verifier failure, not source failure.
- [ ] No approval, closure, or evidence sufficiency claim is made.

---

## 12. Evidence Status Rule

This slice does not itself complete EM-003.

This slice only defines what evidence would be needed for future grounding review.

EM-003 remains:

`PARTIAL`

A future change from `PARTIAL` to any stronger status requires separate explicit governance acceptance.

No implicit status promotion is allowed.

---

## 13. Critical Exception Rule

If any Critical exception remains open, final sign-off must not claim:

- approval,
- closure,
- implementation authority,
- evidence sufficiency,
- governance completion,
- EM-003 status promotion.

Open Critical exceptions block closure.

Ambiguous evidence must be treated as insufficient.

Missing evidence must be treated as insufficient.

Verifier exceptions must be treated as fail-closed.

---

## 14. Explicit Non-Approval

This Freeze Pack does not approve implementation.

This Freeze Pack does not approve source changes.

This Freeze Pack does not approve test changes.

This Freeze Pack does not approve committed verifier scripts.

This Freeze Pack does not approve runtime behavior changes.

This Freeze Pack does not approve test behavior changes.

This Freeze Pack does not close EM-003.

This Freeze Pack does not change EM-003 status.

---

## 15. Final State

After this slice, the expected governance state is:

text
Slice 1.4: PROPOSED
Implementation Authority: NONE
Approval Status: NOT APPROVED
Classification: Governance / Evidence / Documentation Only
EM-003: PARTIAL

This state is intentionally fail-closed.
