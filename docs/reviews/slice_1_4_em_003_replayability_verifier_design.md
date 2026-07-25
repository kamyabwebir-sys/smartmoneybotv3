# Slice 1.4 — EM-003 Replayability Verifier Design Review

Status: PROPOSED  
Implementation Authority: NONE  
Approval Status: NOT APPROVED  
Classification: Governance / Evidence / Documentation Only

---

## 1. Review Purpose

This document defines the review design for a future independent verifier for EM-003 replayability grounding.

The verifier is not approved for commit by this document.

The verifier design is intended only to describe what a future local evidence-producing verification activity must prove.

The review target is narrow:

`DiscoveryRegistry.list_ids()`

The review must determine whether the output of `list_ids()` is deterministic across different registration orders when the registered discovery ID set is identical.

---

## 2. Governance Boundary

This review design grants no implementation authority.

Allowed by this document:

- describe verifier behavior,
- describe replay scenarios,
- describe evidence requirements,
- describe fail-closed rules,
- describe non-conformance interpretation.

Not allowed by this document:

- modifying `src/`,
- modifying `tests/`,
- committing verifier scripts,
- changing runtime behavior,
- changing test behavior,
- changing package/module layout,
- renaming packages,
- moving modules,
- adding framework boundaries,
- introducing execution/trading behavior,
- introducing risk calculation,
- introducing ML decisioning,
- introducing reporting/UI behavior into core/domain logic.

---

## 3. Review Subject

The subject under review is the existing behavior of:
```python
DiscoveryRegistry.list_ids()

The expected property is:

text
Given the same set of discovery IDs,
list_ids() must return the same canonical sorted tuple,
regardless of registration order.

This review does not evaluate:

- discovery execution,
- strategy selection,
- trading decisions,
- risk decisions,
- ML scoring,
- reporting output,
- dashboard behavior,
- Telegram behavior,
- adapter behavior.

---

## 4. Required Dummy Discovery Shape

Any future local verifier object must conform to the existing discovery protocol shape.

The verifier dummy object must expose:

python
@property
def discovery_id(self) -> str:
...

and:

python
def discover(self, context):
...

The `discover(context)` method must not perform meaningful behavior.

It may raise a controlled non-runtime-use error if invoked, because this review must not execute discovery logic.

The verifier must use the registry only for registration and ID listing behavior.

---

## 5. Baseline

The baseline discovery ID set is exactly:

text
zeta.discovery
alpha.discovery
middle.discovery

The canonical expected output is exactly:

python
("alpha.discovery", "middle.discovery", "zeta.discovery")

This canonical output is the only acceptable output for all scenarios.

---

## 6. Scenario Matrix

### Scenario A

Input registration order:

python
("zeta.discovery", "alpha.discovery", "middle.discovery")

Expected output:

python
("alpha.discovery", "middle.discovery", "zeta.discovery")

### Scenario B

Input registration order:

python
("middle.discovery", "zeta.discovery", "alpha.discovery")

Expected output:

python
("alpha.discovery", "middle.discovery", "zeta.discovery")

### Scenario C

Input registration order:

python
("alpha.discovery", "middle.discovery", "zeta.discovery")

Expected output:

python
("alpha.discovery", "middle.discovery", "zeta.discovery")

---

## 7. Verifier Algorithm Design

A future local-only verifier should follow this logical sequence:

1. Import `DiscoveryRegistry`.
2. Define a protocol-conforming dummy discovery object.
3. For each scenario:
   - create a new `DiscoveryRegistry`,
   - register dummy discoveries in the scenario order,
   - call `list_ids()`,
   - capture the observed tuple,
   - compare it to the canonical expected tuple.
4. Record pass/fail per scenario.
5. Fail closed on any mismatch.
6. Fail closed on any exception.
7. Fail closed if evidence is missing or ambiguous.
8. Confirm no `src/` change occurred.
9. Confirm no `tests/` change occurred.
10. Confirm no verifier script was committed unless separately authorized.

---

## 8. Example Non-Committed Verifier Sketch

This sketch is illustrative only.

It is not approved as a committed artifact by this document.

python
from dataclasses import dataclass
from smart_money.discovery.registry import DiscoveryRegistry


@dataclass(frozen=True)
class DummyDiscovery:
value: str

@property
def discovery_id(self) -> str:
return self.value

def discover(self, context):
raise RuntimeError("DummyDiscovery.discover must not be invoked by replayability verifier.")


EXPECTED = ("alpha.discovery", "middle.discovery", "zeta.discovery")

SCENARIOS = {
"A": ("zeta.discovery", "alpha.discovery", "middle.discovery"),
"B": ("middle.discovery", "zeta.discovery", "alpha.discovery"),
"C": ("alpha.discovery", "middle.discovery", "zeta.discovery"),
}


for name, order in SCENARIOS.items():
registry = DiscoveryRegistry()

for discovery_id in order:
registry.register(DummyDiscovery(discovery_id))

observed = registry.list_ids()

if observed != EXPECTED:
raise AssertionError(
f"Scenario {name} failed: observed={observed!r}, expected={EXPECTED!r}"
)

print("EM-003 replayability verifier sketch passed all scenarios.")

The sketch must remain non-authoritative unless a future Freeze Pack explicitly authorizes a committed verifier artifact.

---

## 9. Known Prior Failure

A previous verifier attempt failed with:

text
AttributeError: 'ReplayObject' object has no attribute 'discovery_id'

This means the verifier object did not conform to the expected discovery protocol shape.

Correct interpretation:

text
Verifier non-conformance.

Incorrect interpretation:

text
Source-code defect.

Correct governance response:

text
Fix verifier design.
Do not modify src/.
Do not modify tests/.
Do not change DiscoveryRegistry.
Do not change StructureDiscovery.

---

## 10. Evidence Record Shape

Future evidence should include the following fields:

text
Evidence ID:
Slice:
Commit:
Branch:
OS:
Python version:
Command:
Baseline IDs:
Expected canonical output:
Scenario A registration order:
Scenario A observed output:
Scenario A result:
Scenario B registration order:
Scenario B observed output:
Scenario B result:
Scenario C registration order:
Scenario C observed output:
Scenario C result:
Exceptions:
src/ modified:
tests/ modified:
Committed verifier artifact added:
Overall result:
Reviewer notes:

Required interpretation:

- If all scenarios match the expected tuple, the verifier result may be recorded as pass evidence.
- If any scenario mismatches, evidence is fail-closed.
- If any exception occurs, evidence is fail-closed.
- If `src/` changed, evidence is invalid for Slice 1.4.
- If `tests/` changed, evidence is invalid for Slice 1.4.
- If a verifier artifact was committed without explicit authority, evidence is invalid for Slice 1.4.
- If evidence is incomplete, evidence is insufficient.

---

## 11. Fail-Closed Rules

The verifier review must fail closed if:

- the verifier object lacks `discovery_id`,
- the verifier object does not provide `discover(context)`,
- the verifier invokes discovery execution behavior,
- any scenario output differs from the expected canonical tuple,
- the baseline ID set changes,
- the expected canonical tuple changes,
- output is not captured,
- exceptions are omitted,
- command invocation is omitted,
- environment metadata is omitted,
- `src/` is modified,
- `tests/` is modified,
- committed verifier artifacts are introduced without explicit authority,
- results are ambiguous,
- claims exceed evidence.

---

## 12. Review Acceptance Criteria

This verifier design review is acceptable only if:

- [ ] It remains documentation-only.
- [ ] It does not authorize committed verifier scripts.
- [ ] It does not authorize source changes.
- [ ] It does not authorize test changes.
- [ ] It defines a protocol-conforming dummy discovery shape.
- [ ] It defines the exact baseline ID set.
- [ ] It defines the exact expected canonical output.
- [ ] It defines scenarios A, B, and C.
- [ ] It defines fail-closed handling.
- [ ] It treats prior `discovery_id` failure as verifier non-conformance.
- [ ] It does not claim EM-003 approval.
- [ ] It does not claim EM-003 closure.
- [ ] It does not promote EM-003 from `PARTIAL`.

---

## 13. Final Review Position

This document is a verifier design review only.

It does not produce final evidence.

It does not close EM-003.

It does not approve implementation.

It does not approve test changes.

It does not approve committed verifier artifacts.

The resulting posture remains:

text
EM-003: PARTIAL
Approval Status: NOT APPROVED
Implementation Authority: NONE

This is intentionally fail-closed.
