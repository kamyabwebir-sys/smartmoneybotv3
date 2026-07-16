# Slice 0.11 Freeze Pack

## Slice Title

Domain Event Envelope and Error Contracts

## Current Repository Context

`src/smart_money/core/` already exists and already contains `__init__.py`.

Existing imports already use the `smart_money.core` namespace from both `src` and `tests`.

This slice must not create a new package boundary, rename packages, move modules, or introduce an o3 architecture refactor. It only adds two narrow contract-level modules to the existing core package.

## Target Architecture Notes

The long-term target architecture remains:

- Core
- Domain
- Application
- Adapters
- Analytics
- Reporting

For this slice, the target architecture is only background context. The current repository structure and active Freeze Pack take priority.

This slice adds deterministic core contracts only. It does not reorganize the repository toward the long-term architecture.

## Current Slice Scope

Add the following files:

- `src/smart_money/core/events.py`
- `src/smart_money/core/errors.py`
- `tests/test_domain_events.py`
- `tests/test_domain_errors.py`

## Contract: DomainEventEnvelope

`DomainEventEnvelope` is an immutable, deterministic event envelope contract.

Fields:

- `event_id: str`
- `event_type: str`
- `occurred_at: str`
- `payload: Mapping[str, Any]`
- `metadata: Mapping[str, Any]`

Validation rules:

- `event_id` must be a non-empty string.
- `event_type` must be a non-empty string.
- `occurred_at` must be a non-empty string.
- Whitespace-only strings are invalid.
- Non-string values for required string fields raise `ValueError`.

Behavior:

- Uses `@dataclass(frozen=True)`.
- `payload` defaults to an empty mapping.
- `metadata` defaults to an empty mapping.
- `payload` is defensively copied.
- `metadata` is defensively copied.
- `payload` and `metadata` are shallowly immutable through the envelope.
- Deep immutability of nested values is out of scope.
- `to_dict()` returns a plain deterministic `dict`.
- `to_dict()` does not perform canonical JSON serialization.
- `to_dict()` does not generate IDs, timestamps, or derived fields.

Expected `to_dict()` shape:
```python
{
"event_id": "...",
"event_type": "...",
"occurred_at": "...",
"payload": {...},
"metadata": {...},
}

## Contract: DomainError

`DomainError` is an immutable, deterministic domain error contract.

Fields:

- `code: str`
- `message: str`
- `details: Mapping[str, Any]`

Validation rules:

- `code` must be a non-empty string.
- `message` must be a non-empty string.
- Whitespace-only strings are invalid.
- Non-string values for required string fields raise `ValueError`.

Behavior:

- Uses `@dataclass(frozen=True)`.
- Does not subclass `Exception`.
- `details` defaults to an empty mapping.
- `details` is defensively copied.
- `details` is shallowly immutable through the error object.
- Deep immutability of nested values is out of scope.
- `to_dict()` returns a plain deterministic `dict`.
- `to_dict()` does not perform canonical JSON serialization.
- `to_dict()` does not generate derived fields.

Expected `to_dict()` shape:

python
{
"code": "...",
"message": "...",
"details": {...},
}

## Out-of-Scope Items

The following are explicitly out of scope for Slice 0.11:

- Event bus
- Message broker integration
- Persistence
- Replay engine changes
- Audit log changes
- Runtime exception hierarchy
- Subclassing `Exception`
- Async handling
- Dependency injection
- Global registry
- Package rename
- Module relocation
- New architecture directory creation
- Auto-generating IDs
- Auto-generating timestamps
- UUID generation
- Random values
- Deep freezing nested payload, metadata, or detail values
- Reporting or UI integration
- Trading or execution logic
- Risk calculation
- ML decisioning

## Minimal Proposed Changes

Implementation should be limited to:

- Add `DomainEventEnvelope` in `src/smart_money/core/events.py`.
- Add `DomainError` in `src/smart_money/core/errors.py`.
- Add focused unit tests for event envelope behavior.
- Add focused unit tests for domain error behavior.

No existing core files should be modified unless a failing import or test proves a minimal compatibility change is required.

## Tests: DomainEventEnvelope

`tests/test_domain_events.py` must cover:

- Valid envelope creation.
- Empty `event_id` is rejected.
- Empty `event_type` is rejected.
- Empty `occurred_at` is rejected.
- Whitespace-only required string fields are rejected.
- Non-string `event_id` is rejected with `ValueError`.
- Non-string `event_type` is rejected with `ValueError`.
- Non-string `occurred_at` is rejected with `ValueError`.
- Default `payload` is empty.
- Default `metadata` is empty.
- Payload is defensively copied.
- Metadata is defensively copied.
- Envelope is immutable.
- `to_dict()` returns a plain deterministic dict.

## Tests: DomainError

`tests/test_domain_errors.py` must cover:

- Valid error creation.
- Empty `code` is rejected.
- Empty `message` is rejected.
- Whitespace-only required string fields are rejected.
- Non-string `code` is rejected with `ValueError`.
- Non-string `message` is rejected with `ValueError`.
- Default `details` is empty.
- Details are defensively copied.
- Error is immutable.
- `to_dict()` returns a plain deterministic dict.

## Validation Commands

Run from repository root:

powershell
pytest tests/test_domain_events.py tests/test_domain_errors.py
pytest
git diff --check
git status --short

## Commit Message

text
Docs: add Slice 0.11 freeze pack

Implementation commit, after code and tests pass:

text
Slice 0.11: add domain event and error contracts
