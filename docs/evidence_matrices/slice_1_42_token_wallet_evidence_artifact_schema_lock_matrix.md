# Slice 1.42 — Token and Wallet Evidence Artifact Schema Lock Matrix

| Requirement | Expected Evidence | Status Rule |
| --- | --- | --- |
| Governance-only | Freeze pack and review explicitly state governance-only | REQUIRED |
| Implementation Authority: NO | Review explicitly denies implementation authority | REQUIRED |
| Runtime Authority: NO | Freeze pack explicitly denies runtime authority | REQUIRED |
| Schema lock present | Freeze pack locks token/wallet evidence artifact schema | REQUIRED |
| Deterministic | Freeze pack states deterministic | REQUIRED |
| Replayable | Freeze pack states replayable | REQUIRED |
| Read-only | Freeze pack states read-only | REQUIRED |
| Boundary-safe | Freeze pack defines allowed boundary statuses | REQUIRED |
| Auditable | Freeze pack states auditable | REQUIRED |
| Forbidden semantics blocked | Freeze pack explicitly lists forbidden semantics | REQUIRED |
| Protected paths unchanged | Verifier compares protected hashes | REQUIRED |
| Receipt contract present | Verifier writes governance receipt JSON | REQUIRED |