# install_slice_0_1.ps1
# Installs Slice 0.1 - Foundation Governance Pack for smartmoneybotv3

param(
    [string]$ProjectRoot = ".",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[Slice 0.1] $Message" -ForegroundColor Cyan
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

Write-Step "Installing foundation governance pack into: $RootPath"

New-DirectoryIfMissing -Path (Join-Path $RootPath "docs")
New-DirectoryIfMissing -Path (Join-Path $RootPath "tests")
New-DirectoryIfMissing -Path (Join-Path $RootPath "scripts")

Write-Step "Writing foundation docs"

Write-TextFile -Path (Join-Path $RootPath "docs\build_plan_v1.md") -Content @'
# Build Plan v1

Status: Frozen for Slice 0.1

## Purpose

This document defines the initial development sequence for the deterministic smart money system.

## Target Pipeline

Candles -> Structure/Context -> Setup -> Decision -> Alert

## Core Principles

- deterministic
- replayable
- strict core boundaries
- no execution logic in core
- no risk management logic in core
- no ML decisioning in core
- reporting separated from truth generation

## Planned Early Slice Order

1. Slice 0.1 - foundation governance pack
2. Slice 0.2 - repo skeleton and smoke tests
3. Slice 0.3 - semantic freeze
4. Slice 0.4 - contract shape freeze
5. Slice 0.5 - Python contract skeletons
6. Slice 0.6+ - validation, serialization, ids, and engines in controlled order
'@

Write-TextFile -Path (Join-Path $RootPath "docs\scope_guardrails_v1.md") -Content @'
# Scope Guardrails v1

Status: Frozen for Slice 0.1

## Allowed in Core

- candle-based deterministic analysis
- structure and context derivation
- setup qualification
- decision classification
- alert generation
- evidence and reason code attachment

## Forbidden in Core

- trade execution
- broker side effects
- wallet side effects
- portfolio management
- discretionary override
- hidden mutable state
- ML-driven truth generation
- UI-specific formatting as core truth

## Delivery Rules

- English code
- Persian reporting later
- immutable models
- canonical serialization
- explicit schema versioning
'@

Write-TextFile -Path (Join-Path $RootPath "docs\domain_glossary_seed_v1.md") -Content @'
# Domain Glossary Seed v1

Status: Seed for Slice 0.1

This file is intentionally brief.
Detailed semantics are frozen later.

## Seed Terms

- candle
- structure
- context
- setup
- decision
- alert
- evidence
- reason code
- risk flag
- deterministic replay
- canonical serialization
- schema version
'@

Write-TextFile -Path (Join-Path $RootPath "docs\core_contracts_index_v1.md") -Content @'
# Core Contracts Index v1

Status: Index only for Slice 0.1

This index lists contract families expected in future slices.

## Expected Contract Families

- Candle
- StructureEvent
- ContextState
- SetupCandidate
- DecisionRecord
- AlertRecord
- EvidenceItem
- RiskFlag

Detailed semantics and shape are deferred to later slices.
'@

Write-Step "Writing foundation tests"

Write-TextFile -Path (Join-Path $RootPath "tests\test_foundation_docs_exist.py") -Content @'
from pathlib import Path


def test_foundation_docs_exist() -> None:
    root = Path(__file__).resolve().parents[1]

    expected = [
        root / "docs" / "build_plan_v1.md",
        root / "docs" / "scope_guardrails_v1.md",
        root / "docs" / "domain_glossary_seed_v1.md",
        root / "docs" / "core_contracts_index_v1.md",
    ]

    for path in expected:
        assert path.exists(), f"Missing foundation doc: {path}"
'@

Write-TextFile -Path (Join-Path $RootPath "tests\test_foundation_keywords.py") -Content @'
from pathlib import Path


def _read_doc(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_build_plan_has_pipeline() -> None:
    root = Path(__file__).resolve().parents[1]
    content = _read_doc(root / "docs" / "build_plan_v1.md")

    required_terms = [
        "Candles -> Structure/Context -> Setup -> Decision -> Alert",
        "deterministic",
        "replayable",
        "strict core boundaries",
    ]

    for term in required_terms:
        assert term in content, f"Missing build plan term: {term}"


def test_scope_guardrails_define_forbidden_items() -> None:
    root = Path(__file__).resolve().parents[1]
    content = _read_doc(root / "docs" / "scope_guardrails_v1.md")

    required_terms = [
        "trade execution",
        "portfolio management",
        "ML-driven truth generation",
        "canonical serialization",
    ]

    for term in required_terms:
        assert term in content, f"Missing guardrail term: {term}"


def test_contract_index_lists_expected_families() -> None:
    root = Path(__file__).resolve().parents[1]
    content = _read_doc(root / "docs" / "core_contracts_index_v1.md")

    required_terms = [
        "Candle",
        "StructureEvent",
        "ContextState",
        "SetupCandidate",
        "DecisionRecord",
        "AlertRecord",
        "EvidenceItem",
        "RiskFlag",
    ]

    for term in required_terms:
        assert term in content, f"Missing contract family: {term}"
'@

Write-Step "Slice 0.1 installation complete"
Write-Host ""
Write-Host "Next commands:" -ForegroundColor White
Write-Host "  python -m pytest" -ForegroundColor Green
