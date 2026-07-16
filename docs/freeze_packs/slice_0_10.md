# Freeze Pack: Slice 0.10 - Deterministic Structure Discovery Registry

## Status

Frozen for implementation.

## Slice Name

Deterministic Structure Discovery Registry

## Purpose

Introduce a minimal deterministic registry for market-structure discovery components.

This slice creates a small infrastructure contract for registering, listing, and retrieving structure discovery components by stable identifiers.

It does not implement market-structure algorithms.

## Architectural Context

The long-term target architecture is:

- Core
- Domain
- Application
- Adapters
- Analytics
- Reporting

This target architecture is accepted as future direction only.

Slice 0.10 must not refactor the repository toward the target architecture. Current repository stability and the active Freeze Pack take priority over architectural cleanliness.

## Authoritative Files

The authoritative implementation and test files for this slice are:

- `src/smart_money/discovery/registry.py`
- `tests/discovery/test_registry.py`

A tiny export update is allowed only if strictly necessary:

- `src/smart_money/discovery/__init__.py`

## Allowed Changes

This slice may introduce or update:

- A minimal immutable `DiscoveryResult` contract.
- A typed `StructureDiscovery` protocol or equivalent interface.
- A `DiscoveryRegistry` for deterministic registration and lookup.
- Focused pytest coverage for registry behavior.

## Required Behavior

The registry must support:

- Registering a discovery component by stable string identifier.
- Retrieving a registered discovery by identifier.
- Listing registered discovery identifiers in deterministic lexicographic order.
- Rejecting duplicate discovery identifiers.
- Rejecting lookup of unknown discovery identifiers.
- Keeping value contracts immutable where appropriate.

## Determinism Requirements

The implementation must not depend on:

- Runtime randomness.
- Current time.
- Filesystem ordering.
- Network access.
- Environment-specific behavior.
- External services.
- Non-deterministic iteration behavior exposed through public API.

Public listing behavior must be stable and deterministic. `list_ids()` must return identifiers in sorted lexicographic order, not insertion order.

## Suggested Public API

The final implementation may vary slightly if existing code requires it, but the scope should remain equivalent to:

```python
from dataclasses import dataclass
from typing import Mapping, Protocol


@dataclass(frozen=True)
class DiscoveryResult:
    discovery_id: str
    payload: Mapping[str, object]


class StructureDiscovery(Protocol):
    @property
    def discovery_id(self) -> str:
        ...

    def discover(self, context: Mapping[str, object]) -> DiscoveryResult:
        ...


class DiscoveryRegistry:
    def register(self, discovery: StructureDiscovery) -> None:
        ...

    def get(self, discovery_id: str) -> StructureDiscovery:
        ...

    def list_ids(self) -> tuple[str, ...]:
        ...

## Error Semantics

Use simple explicit Python exceptions.

Required behavior:

- Duplicate registration: `ValueError`
- Unknown discovery lookup: `KeyError`

Error messages should be stable and clear enough for tests.

No custom exception hierarchy is required in this slice.

## Tests Required

Add or update focused tests in:

- `tests/discovery/test_registry.py`

Required coverage:

- Successful registration and lookup.
- Deterministic lexicographic listing of registered discovery identifiers.
- Duplicate discovery identifier rejection.
- Unknown discovery identifier lookup rejection.
- Immutability of `DiscoveryResult`.

Suggested test names:

- `test_register_and_get_discovery`
- `test_list_ids_is_deterministic`
- `test_duplicate_discovery_id_is_rejected`
- `test_unknown_discovery_id_is_rejected`
- `test_discovery_result_is_immutable`

## Invariants

- Registry output order is deterministic and lexicographic.
- Registry identifiers are stable strings.
- Discovery contracts are minimal.
- Value objects are immutable where appropriate.
- No algorithmic market-structure logic is introduced.
- No dependencies are added.
- No package or module moves are performed.
- No target architecture folders are created.

## Out of Scope

The following are explicitly out of scope:

- Candle model.
- Timeframe model.
- Swing high / swing low detection.
- BOS / CHoCH detection.
- Setup generation.
- Decision logic.
- Alert logic.
- Risk calculation.
- Execution or trading logic.
- Wallet intelligence.
- Analytics scoring.
- Reporting or UI output.
- Replay event log.
- Replay harness.
- Snapshot store.
- Framework/package boundary checks.
- Renaming the `smart_money` package.
- Moving `src/smart_money/core/config.py`.
- Creating `domain`, `application`, `adapters`, `analytics`, or `reporting` package trees.

## Validation Commands

Run:

bash
pytest tests/discovery/test_registry.py
pytest
git diff --check

## Completion Criteria

Slice 0.10 is complete when:

- The registry contract exists.
- Registry behavior is deterministic.
- `list_ids()` returns sorted lexicographic identifiers.
- Duplicate and missing lookup behavior is tested.
- Immutability is tested.
- The allowed test suite passes.
- No out-of-scope architecture or domain logic has been added.


**پرامپت Claude Code**

این را الان به Claude بده:

```text
Project: SmartMoneyBotV3
Role: Coding Agent

Task:
Implement Slice 0.10 exactly according to the Freeze Pack below.

Active Slice:
Slice 0.10 - Deterministic Structure Discovery Registry

Project rules:
- The project is deterministic, replayable, and slice-based.
- Keep changes narrow and test-focused.
- Do not perform broad cleanup.
- Do not perform package rename.
- Do not move modules.
- Do not create future architecture folder trees.
- Do not introduce dependencies.

Long-term Target Architecture:
- Core
- Domain
- Application
- Adapters
- Analytics
- Reporting

Important:
The Target Architecture is future direction only.
Do not refactor the repository to match it in this slice.

Authoritative files:
- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

You may touch this file only if strictly necessary for exports:
- src/smart_money/discovery/__init__.py

Freeze Pack:

# Freeze Pack: Slice 0.10 - Deterministic Structure Discovery Registry

## Status

Frozen for implementation.

## Slice Name

Deterministic Structure Discovery Registry

## Purpose

Introduce a minimal deterministic registry for market-structure discovery components.

This slice creates a small infrastructure contract for registering, listing, and retrieving structure discovery components by stable identifiers.

It does not implement market-structure algorithms.

## Architectural Context

The long-term target architecture is:

- Core
- Domain
- Application
- Adapters
- Analytics
- Reporting

This target architecture is accepted as future direction only.

Slice 0.10 must not refactor the repository toward the target architecture. Current repository stability and the active Freeze Pack take priority over architectural cleanliness.

## Authoritative Files

The authoritative implementation and test files for this slice are:

- src/smart_money/discovery/registry.py
- tests/discovery/test_registry.py

A tiny export update is allowed only if strictly necessary:

- src/smart_money/discovery/__init__.py

## Allowed Changes

This slice may introduce or update:

- A minimal immutable DiscoveryResult contract.
- A typed StructureDiscovery protocol or equivalent interface.
- A DiscoveryRegistry for deterministic registration and lookup.
- Focused pytest coverage for registry behavior.

## Required Behavior

The registry must support:

- Registering a discovery component by stable string identifier.
- Retrieving a registered discovery by identifier.
- Listing registered discovery identifiers in deterministic lexicographic order.
- Rejecting duplicate discovery identifiers.
- Rejecting lookup of unknown discovery identifiers.
- Keeping value contracts immutable where appropriate.

## Determinism Requirements

The implementation must not depend on:

- Runtime randomness.
- Current time.
- Filesystem ordering.
- Network access.
- Environment-specific behavior.
- External services.
- Non-deterministic iteration behavior exposed through public API.

Public listing behavior must be stable and deterministic. list_ids() must return identifiers in sorted lexicographic order, not insertion order.

## Required Public API

Implement a minimal API equivalent to this, unless existing code requires a very small adjustment:

```python
from dataclasses import dataclass
from typing import Mapping, Protocol


@dataclass(frozen=True)
class DiscoveryResult:
    discovery_id: str
    payload: Mapping[str, object]


class StructureDiscovery(Protocol):
    @property
    def discovery_id(self) -> str:
        ...

    def discover(self, context: Mapping[str, object]) -> DiscoveryResult:
        ...


class DiscoveryRegistry:
    def register(self, discovery: StructureDiscovery) -> None:
        ...

    def get(self, discovery_id: str) -> StructureDiscovery:
        ...

    def list_ids(self) -> tuple[str, ...]:
        ...

Implementation requirements:
- Store discoveries internally by discovery_id.
- Reject duplicate discovery_id with ValueError.
- Reject unknown discovery_id lookup with KeyError.
- list_ids() must return tuple[str, ...].
- list_ids() must return identifiers in sorted lexicographic order, not insertion order.
- Do not call discover() inside register().
- Do not add algorithmic discovery behavior.
- Keep code simple and readable.

## Error Semantics

Use simple explicit Python exceptions.

Required behavior:

- Duplicate registration: ValueError
- Unknown discovery lookup: KeyError

Error messages should be stable and clear enough for tests.

No custom exception hierarchy is required in this slice.

## Tests Required

Add or update focused tests in:

- tests/discovery/test_registry.py

Required coverage:

- Successful registration and lookup.
- Deterministic lexicographic listing of registered discovery identifiers.
- Duplicate discovery identifier rejection.
- Unknown discovery identifier lookup rejection.
- Immutability of DiscoveryResult.

Use pytest.

Suggested test names:
- test_register_and_get_discovery
- test_list_ids_is_deterministic
- test_duplicate_discovery_id_is_rejected
- test_unknown_discovery_id_is_rejected
- test_discovery_result_is_immutable

## Invariants

- Registry output order is deterministic and lexicographic.
- Registry identifiers are stable strings.
- Discovery contracts are minimal.
- Value objects are immutable where appropriate.
- No algorithmic market-structure logic is introduced.
- No dependencies are added.
- No package or module moves are performed.
- No target architecture folders are created.

## Out of Scope

The following are explicitly out of scope:

- Candle model.
- Timeframe model.
- Swing high / swing low detection.
- BOS / CHoCH detection.
- Setup generation.
- Decision logic.
- Alert logic.
- Risk calculation.
- Execution or trading logic.
- Wallet intelligence.
- Analytics scoring.
- Reporting or UI output.
- Replay event log.
- Replay harness.
- Snapshot store.
- Framework/package boundary checks.
- Renaming the smart_money package.
- Moving src/smart_money/core/config.py.
- Creating domain, application, adapters, analytics, or reporting package trees.

## Validation Commands

Run:

bash
pytest tests/discovery/test_registry.py
pytest
git diff --check

Implementation instructions:
1. Inspect the current repository files first.
2. Modify only the allowed files.
3. Keep the diff minimal.
4. Add or update focused tests.
5. Run the validation commands.
6. Report the result.

Final response format:
1. What changed
2. Tests added or updated
3. Validation results
4. Future work, only if relevant

Do not include broad architecture recommendations.
Do not implement anything outside Slice 0.10.