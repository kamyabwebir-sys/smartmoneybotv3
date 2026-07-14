# install_slice_0_4.ps1
# Installs Slice 0.4 - Core Contract Shape Spec for smartmoneybotv3

param(
    [string]$ProjectRoot = ".",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[Slice 0.4] $Message" -ForegroundColor Cyan
}

function New-DirectoryIfMissing {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path | Out-Null
    }
}

function Write-TextFile {
    param(
        [string]$Path,
        [string]$Content
    )

    if ((Test-Path -LiteralPath $Path) -and (-not $Force)) {
        Write-Host "SKIP existing file: $Path" -ForegroundColor Yellow
        return
    }

    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-DirectoryIfMissing -Path $parent
    }

    Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
    Write-Host "WRITE $Path" -ForegroundColor Green
}

$Root = Resolve-Path $ProjectRoot
$RootPath = $Root.Path

Write-Step "Installing contract shape freeze docs into: $RootPath"

New-DirectoryIfMissing -Path (Join-Path $RootPath "docs")
New-DirectoryIfMissing -Path (Join-Path $RootPath "tests")
New-DirectoryIfMissing -Path (Join-Path $RootPath "scripts")

Write-Step "Writing contract shape spec documents"

Write-TextFile -Path (Join-Path $RootPath "docs\core_contract_shape_v1.md") -Content @'
# Core Contract Shape v1

Status: Frozen for Slice 0.4

## Purpose

This document freezes the structural shape of core contracts before engine implementation.

It follows the architecture rule that contracts must be defined before engines.
It also prepares future schema validation, invariant enforcement, backward compatibility gates,
deterministic serialization, and deterministic ids.

This document defines shape, not business logic implementation.

---

## 1. Global Design Rules

All core contracts must be:

- immutable in intent
- deterministic in meaning
- replay-stable
- serializable through canonical JSON
- versioned explicitly
- explainable through evidence and reason codes
- separated from UI/report rendering concerns

Core contracts must not embed:

- execution side effects
- runtime-only mutable state
- network dependencies
- presentation-only Persian text
- adapter-specific transport payloads

---

## 2. Shared Contract Field Policy

The following concepts are mandatory across most event-like and record-like core contracts.

### Mandatory Shared Fields

- `schema_version`: `str`
- `contract_type`: `str`
- `id`: `str`
- `occurred_at`: timezone-aware UTC datetime
- `created_at`: timezone-aware UTC datetime
- `market`: `str`
- `symbol`: `str`
- `timeframe`: `str`

### Optional Shared Fields

- `evidence_ref`: `str | None`
- `reason_code`: `str | None`
- `risk_flags`: collection or `None`
- `tags`: collection or `None`
- `metadata`: mapping or `None`

### Shared Semantic Notes

- `occurred_at` is the logical event time.
- `created_at` is the contract creation timestamp inside the pipeline.
- `id` must be deterministic once deterministic id rules are frozen.
- `contract_type` must remain stable across minor refactors.
- `schema_version` must be explicit and never inferred.

---

## 3. Core Primitive Contracts

This slice freezes the minimum expected contract families.

### 3.1 Candle

Purpose: canonical closed interval market observation.

Expected fields:

- `schema_version`
- `contract_type`
- `id`
- `market`
- `symbol`
- `timeframe`
- `open_time`
- `close_time`
- `open_price`
- `high_price`
- `low_price`
- `close_price`
- `volume`
- `trade_count`
- `source_ref`
- `created_at`

Invariant expectations:

- `open_time < close_time`
- `high_price >= open_price`
- `high_price >= close_price`
- `high_price >= low_price`
- `low_price <= open_price`
- `low_price <= close_price`
- prices must be non-negative
- volume must be non-negative
- candle must represent a closed interval only

### 3.2 StructureEvent

Purpose: normalized structural event such as BOS, CHOCH, or sweep.

Expected fields:

- `schema_version`
- `contract_type`
- `id`
- `event_type`
- `market`
- `symbol`
- `timeframe`
- `occurred_at`
- `reference_level`
- `direction`
- `reference_id`
- `evidence_ref`
- `reason_code`
- `created_at`

Invariant expectations:

- `event_type` must be from a frozen symbolic set
- `direction` must be from a frozen symbolic set
- `reference_id` must not be empty
- `reason_code` must align with event semantics when present

### 3.3 ContextState

Purpose: deterministic interpretive state around current price action.

Expected fields:

- `schema_version`
- `contract_type`
- `id`
- `market`
- `symbol`
- `timeframe`
- `occurred_at`
- `structural_bias`
- `liquidity_position`
- `active_imbalances`
- `active_risk_flags`
- `evidence_ref`
- `created_at`

Invariant expectations:

- context is descriptive, not executable
- active collections must be deterministic in order or canonically sortable
- bias values must come from a frozen symbolic vocabulary

### 3.4 SetupCandidate

Purpose: intermediate candidate eligible for downstream decision evaluation.

Expected fields:

- `schema_version`
- `contract_type`
- `id`
- `market`
- `symbol`
- `timeframe`
- `occurred_at`
- `setup_type`
- `status`
- `context_ref`
- `evidence_ref`
- `reason_code`
- `created_at`

Invariant expectations:

- setup candidate is not execution permission
- `context_ref` must point to a valid context object when present
- `status` must be a frozen symbolic value

### 3.5 DecisionRecord

Purpose: deterministic outcome of analysis over a setup/context state.

Expected fields:

- `schema_version`
- `contract_type`
- `id`
- `market`
- `symbol`
- `timeframe`
- `occurred_at`
- `decision_type`
- `setup_ref`
- `context_ref`
- `evidence_ref`
- `reason_code`
- `risk_flags`
- `created_at`

Invariant expectations:

- decision belongs to analysis only
- every non-trivial decision should be explainable by evidence and/or reason code
- `decision_type` must be frozen symbolic vocabulary

### 3.6 AlertRecord

Purpose: reportable emitted analytical event.

Expected fields:

- `schema_version`
- `contract_type`
- `id`
- `market`
- `symbol`
- `timeframe`
- `occurred_at`
- `alert_type`
- `decision_ref`
- `severity`
- `reason_code`
- `created_at`

Invariant expectations:

- alert is not execution
- alert must derive from deterministic upstream state
- severity must be from frozen symbolic vocabulary

### 3.7 EvidenceItem

Purpose: machine-readable justification fragment.

Expected fields:

- `schema_version`
- `contract_type`
- `id`
- `occurred_at`
- `evidence_type`
- `source_ref`
- `context_ref`
- `details`
- `generated_by`
- `created_at`

Invariant expectations:

- evidence must refer to observable deterministic facts
- `details` must remain machine-readable
- evidence must not embed hidden subjective judgment

### 3.8 RiskFlag

Purpose: non-execution analytical caution marker.

Expected fields:

- `schema_version`
- `contract_type`
- `id`
- `occurred_at`
- `flag_type`
- `severity`
- `reason_code`
- `evidence_ref`
- `created_at`

Invariant expectations:

- risk flags annotate caution
- risk flags do not perform risk management
- severity vocabulary must be frozen later but shape is frozen now

---

## 4. Type Policy

Recommended core type choices:

- `Decimal` for price, volume, amount, size, threshold-like values
- timezone-aware UTC `datetime` for timestamps
- `str` for ids, codes, names, symbols, references
- `int` for counts, indices, sequence-like values
- `bool` for explicit binary flags
- `tuple` preferred over mutable list in immutable model implementations
- mapping/object fields should be tightly controlled and canonically serialized

Do not use float for canonical financial values.

---

## 5. Nullability Policy

Rules:

- optional absence should be represented as `None` in Python
- canonical JSON should encode absence as `null`
- empty string must not be used to mean missing
- zero must not be used to mean unknown
- false must not be used to mean absent

---

## 6. Serialization Freeze Expectations

Canonical serialization must be stable.

Minimum rules:

- field naming must be stable
- output key ordering must be stable
- Decimal values must preserve exactness
- datetime values must serialize in canonical UTC format
- enum-like symbolic values must serialize as stable strings
- equal semantic objects must produce equal canonical serialized output

Implementation is deferred, but these expectations are frozen now.

---

## 7. Deterministic Id Expectations

Deterministic ids must be locked early.

Current frozen expectations:

- ids must be derived from canonical contract meaning, not random UUIDs
- ids must not depend on memory address, insertion order, or wall-clock accident
- equal canonical inputs must produce equal ids
- changed semantic payload must produce a different id when identity semantics require it

Exact deterministic id construction is deferred.

---

## 8. Backward Compatibility Gates

Contracts must support explicit compatibility thinking.

Allowed without schema major change:

- adding optional fields
- clarifying documentation
- tightening tests that match existing semantics

Breaking changes:

- removing a field
- renaming a field
- changing field meaning
- changing a field type incompatibly
- changing canonical serialization meaning
- changing id semantics

Breaking changes require new schema version and explicit migration note.

---

## 9. Frozen Naming Expectations

- field names: snake_case
- contract classes/types: PascalCase in code, stable strings in serialized form
- ids end with `_id` only when they are named references rather than generic root `id`
- references use `_ref`
- timestamps use `_at` for events and `*_time` for interval boundaries
- booleans use `is_` or `has_`
- collections use plural names
- reason codes remain uppercase snake case

---

## 10. Example Shapes

These are shape examples only.

### Candle Example Shape
```python
@dataclass(frozen=True, slots=True)
class Candle:
schema_version: str
contract_type: str
id: str
market: str
symbol: str
timeframe: str
open_time: datetime
close_time: datetime
open_price: Decimal
high_price: Decimal
low_price: Decimal
close_price: Decimal
volume: Decimal
trade_count: int | None
source_ref: str | None
created_at: datetime

### StructureEvent Example Shape

python
@dataclass(frozen=True, slots=True)
class StructureEvent:
schema_version: str
contract_type: str
id: str
event_type: str
market: str
symbol: str
timeframe: str
occurred_at: datetime
reference_level: Decimal
direction: str
reference_id: str
evidence_ref: str | None
reason_code: str | None
created_at: datetime

### EvidenceItem Example Shape

python
@dataclass(frozen=True, slots=True)
class EvidenceItem:
schema_version: str
contract_type: str
id: str
occurred_at: datetime
evidence_type: str
source_ref: str | None
context_ref: str | None
details: dict[str, object] | None
generated_by: str
created_at: datetime
'@

Write-TextFile -Path (Join-Path $RootPath "docs\naming_conventions_v1.md") -Content @'
# Naming Conventions v1

Status: Frozen for Slice 0.4

## Purpose

This document freezes naming conventions for core contract fields and symbolic values.

## 1. Field Naming

All field names must use snake_case.

Examples:

- `schema_version`
- `contract_type`
- `occurred_at`
- `created_at`
- `open_time`
- `close_time`
- `evidence_ref`
- `reason_code`

## 2. Suffix Rules

### `_ref`
Use for references to another contract object by id.

Examples:

- `evidence_ref`
- `context_ref`
- `setup_ref`
- `decision_ref`
- `source_ref`

### `_id`
Use for named identifier fields that are not the root `id`.

Examples:

- `reference_id`
- `candidate_id`
- `event_id`

### `_at`
Use for event timestamps or creation timestamps.

Examples:

- `occurred_at`
- `created_at`
- `updated_at`

### `_time`
Use for interval boundary times or market interval semantics.

Examples:

- `open_time`
- `close_time`

## 3. Boolean Naming

Booleans must start with:

- `is_`
- `has_`

Examples:

- `is_confirmed`
- `has_evidence`

## 4. Collection Naming

Use plural nouns for collections.

Examples:

- `risk_flags`
- `tags`
- `reason_codes`
- `evidence_items`

## 5. Symbolic Values

### Reason Codes
Reason codes must use UPPERCASE_SNAKE_CASE.

Examples:

- `DECISION_VALID`
- `STRUCTURE_BOS_BULL`
- `RISK_LOW_CONFIDENCE`

### Enum-like Contract Values
Serialized enum-like values should be stable strings.

Examples:

- `bos`
- `choch`
- `sweep`
- `bullish`
- `bearish`
- `valid`
- `blocked`

## 6. Contract Naming in Code

Contract types/classes should use PascalCase.

Examples:

- `Candle`
- `StructureEvent`
- `ContextState`
- `SetupCandidate`
- `DecisionRecord`
- `AlertRecord`
- `EvidenceItem`
- `RiskFlag`

## 7. Avoid

Avoid:

- camelCase field names
- one-letter names
- overloaded ambiguous names
- adapter-specific naming in core contracts
- Persian field names in core code
'@

Write-TextFile -Path (Join-Path $RootPath "docs\backward_compatibility_v1.md") -Content @'
# Backward Compatibility v1

Status: Frozen for Slice 0.4

## Purpose

This document defines compatibility expectations for core contract evolution.

## 1. Compatibility Philosophy

Contract evolution must protect deterministic replay, canonical serialization stability,
and stable interpretation of evidence, reason codes, and ids.

## 2. Allowed Non-Breaking Changes

The following are generally allowed within the same schema line:

- adding an optional field
- clarifying documentation
- adding stricter tests for already-frozen semantics
- adding derived helper functions outside serialized contract shape

## 3. Breaking Changes

The following are breaking:

- removing a field
- renaming a field
- changing field type incompatibly
- changing required/optional meaning in a way that breaks existing consumers
- changing stable symbolic values without migration
- changing canonical serialization meaning
- changing deterministic id semantics
- changing meaning of evidence or reason code references

## 4. Required Response to Breaking Change

When a breaking change is necessary:

- bump schema version explicitly
- document migration rationale
- document old and new meaning
- add compatibility tests or migration notes
- ensure replay consumers know which schema they are reading

## 5. Invariant Tightening

Invariant tightening is allowed only if one of the following is true:

- previous data already satisfied the tighter invariant in practice
- the change is introduced under a new schema version
- migration guidance is documented

## 6. Deterministic Stability Priority

If a proposed change improves convenience but weakens deterministic replay or canonical stability,
the change must be rejected in core contracts.
'@

Write-TextFile -Path (Join-Path $RootPath "docs\slice_0_4_notes.md") -Content @'
# Slice 0.4 Notes

Status: Installed

## Goal

Freeze core contract shapes before engine implementation.

## Why This Exists

This slice follows the principle that contracts should be defined before engines.
It also prepares future schema validation, invariant tests, backward compatibility gates,
deterministic serialization, and deterministic ids.

## Files Added

- docs/core_contract_shape_v1.md
- docs/naming_conventions_v1.md
- docs/backward_compatibility_v1.md
- docs/slice_0_4_notes.md
- tests/test_contract_shape_docs_exist.py
- tests/test_contract_shape_keywords.py
- tests/test_contract_shape_examples.py
- scripts/install_slice_0_4.ps1

## Acceptance Criteria

- contract shape documents exist
- mandatory shape concepts are documented
- naming conventions are frozen
- backward compatibility policy is frozen
- deterministic serialization and deterministic ids are explicitly acknowledged
- tests pass

## Out Of Scope

- production dataclasses
- serializer implementation
- deterministic id algorithm
- schema validator implementation
- engine logic
'@

Write-Step "Writing tests for contract shape freeze"

Write-TextFile -Path (Join-Path $RootPath "tests\test_contract_shape_docs_exist.py") -Content @'
from pathlib import Path


def test_contract_shape_docs_exist() -> None:
root = Path(__file__).resolve().parents[1]

expected = [
root / "docs" / "core_contract_shape_v1.md",
root / "docs" / "naming_conventions_v1.md",
root / "docs" / "backward_compatibility_v1.md",
root / "docs" / "slice_0_4_notes.md",
]

for path in expected:
assert path.exists(), f"Missing contract shape doc: {path}"
'@

Write-TextFile -Path (Join-Path $RootPath "tests\test_contract_shape_keywords.py") -Content @'
from pathlib import Path


def _read_doc(path: Path) -> str:
return path.read_text(encoding="utf-8")


def test_core_contract_shape_keywords_present() -> None:
root = Path(__file__).resolve().parents[1]
content = _read_doc(root / "docs" / "core_contract_shape_v1.md")

required_terms = [
"schema_version",
"contract_type",
"canonical JSON",
"deterministic ids",
"Backward Compatibility Gates",
"Candle",
"StructureEvent",
"ContextState",
"SetupCandidate",
"DecisionRecord",
"AlertRecord",
"EvidenceItem",
"RiskFlag",
"open_time < close_time",
"field naming must be stable",
]

for term in required_terms:
assert term in content, f"Missing contract shape term: {term}"


def test_naming_conventions_keywords_present() -> None:
root = Path(__file__).resolve().parents[1]
content = _read_doc(root / "docs" / "naming_conventions_v1.md")

required_terms = [
"snake_case",
"_ref",
"_id",
"_at",
"_time",
"UPPERCASE_SNAKE_CASE",
"PascalCase",
"camelCase",
]

for term in required_terms:
assert term in content, f"Missing naming convention term: {term}"


def test_backward_compatibility_keywords_present() -> None:
root = Path(__file__).resolve().parents[1]
content = _read_doc(root / "docs" / "backward_compatibility_v1.md")

required_terms = [
"adding an optional field",
"removing a field",
"renaming a field",
"changing deterministic id semantics",
"bump schema version explicitly",
"deterministic replay",
]

for term in required_terms:
assert term in content, f"Missing compatibility phrase: {term}"
'@

Write-TextFile -Path (Join-Path $RootPath "tests\test_contract_shape_examples.py") -Content @'
from pathlib import Path


def _read_doc(path: Path) -> str:
return path.read_text(encoding="utf-8")


def test_example_shapes_include_expected_fields() -> None:
root = Path(__file__).resolve().parents[1]
content = _read_doc(root / "docs" / "core_contract_shape_v1.md")

required_fragments = [
"class Candle:",
"open_price: Decimal",
"close_price: Decimal",
"volume: Decimal",
"class StructureEvent:",
"event_type: str",
"reference_level: Decimal",
"class EvidenceItem:",
"details: dict[str, object] | None",
]

for fragment in required_fragments:
assert fragment in content, f"Missing example shape fragment: {fragment}"


def test_slice_notes_mentions_out_of_scope_items() -> None:
root = Path(__file__).resolve().parents[1]
content = _read_doc(root / "docs" / "slice_0_4_notes.md")

required_terms = [
"production dataclasses",
"serializer implementation",
"deterministic id algorithm",
"engine logic",
]

for term in required_terms:
assert term in content, f"Missing slice note term: {term}"
'@

Write-Step "Slice 0.4 installation complete"
Write-Host ""
Write-Host "Next commands:" -ForegroundColor White
Write-Host "  python -m pytest" -ForegroundColor Green
Write-Host ""
Write-Host "Recommended next slice:" -ForegroundColor White
Write-Host "  Slice 0.5 - Core Contract Python Models (frozen dataclass skeletons only)" -ForegroundColor Green

