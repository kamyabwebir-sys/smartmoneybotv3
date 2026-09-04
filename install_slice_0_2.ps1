# install_slice_0_2.ps1
# Installs Slice 0.2 - Project Skeleton for smartmoneybotv3

param(
    [string]$ProjectRoot = ".",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[Slice 0.2] $Message" -ForegroundColor Cyan
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

Write-Step "Installing project skeleton into: $RootPath"

New-DirectoryIfMissing -Path (Join-Path $RootPath "tests")
New-DirectoryIfMissing -Path (Join-Path $RootPath "scripts")
New-DirectoryIfMissing -Path (Join-Path $RootPath "src\smartmoneybot")
New-DirectoryIfMissing -Path (Join-Path $RootPath "src\smartmoneybot\governance")
New-DirectoryIfMissing -Path (Join-Path $RootPath "src\smartmoneybot\core")
New-DirectoryIfMissing -Path (Join-Path $RootPath "src\smartmoneybot\discovery")
New-DirectoryIfMissing -Path (Join-Path $RootPath "src\smartmoneybot\adapters")
New-DirectoryIfMissing -Path (Join-Path $RootPath "src\smartmoneybot\reporting")
New-DirectoryIfMissing -Path (Join-Path $RootPath "src\smartmoneybot\ai")

Write-Step "Writing pyproject.toml"

Write-TextFile -Path (Join-Path $RootPath "pyproject.toml") -Content @'
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "smartmoneybotv3"
version = "0.1.0"
description = "Deterministic, explainable, replayable market-structure and discovery platform with Persian-first reporting."
readme = "README.md"
requires-python = ">=3.11"
authors = [
  { name = "smartmoneybotv3" }
]
license = { text = "Proprietary" }
dependencies = []

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
  "-ra",
  "--strict-markers",
  "--strict-config"
]
'@

Write-Step "Writing pytest.ini"

Write-TextFile -Path (Join-Path $RootPath "pytest.ini") -Content @'
[pytest]
minversion = 8.0
testpaths = tests
pythonpath = src
addopts = -ra --strict-markers --strict-config
'@

Write-Step "Writing package files"

Write-TextFile -Path (Join-Path $RootPath "src\smartmoneybot\__init__.py") -Content @'
"""smartmoneybotv3 package."""

__all__ = ["__version__"]

__version__ = "0.1.0"
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoneybot\governance\__init__.py") -Content @'
"""Governance, contracts, schema rules, and versioning."""
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoneybot\core\__init__.py") -Content @'
"""Deterministic market-structure core."""
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoneybot\discovery\__init__.py") -Content @'
"""Discovery layer for tokens, wallets, graphs, and anomalies."""
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoneybot\adapters\__init__.py") -Content @'
"""External data adapters and canonical mapping."""
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoneybot\reporting\__init__.py") -Content @'
"""Persian reporting, dashboard read models, and Telegram payload models."""
'@

Write-TextFile -Path (Join-Path $RootPath "src\smartmoneybot\ai\__init__.py") -Content @'
"""AI explanation layer. Not a source of deterministic truth."""
'@

Write-Step "Writing smoke tests"

Write-TextFile -Path (Join-Path $RootPath "tests\test_smoke_import.py") -Content @'
from smartmoneybot import __version__


def test_package_version_is_defined() -> None:
    assert __version__ == "0.1.0"
'@

Write-TextFile -Path (Join-Path $RootPath "tests\test_project_structure.py") -Content @'
from pathlib import Path


def test_expected_top_level_docs_exist() -> None:
    root = Path(__file__).resolve().parents[1]

    expected = [
        root / "docs" / "scope_guardrails.md",
        root / "docs" / "build_plan.md",
        root / "docs" / "architecture_boundaries.md",
        root / "docs" / "open_questions.md",
        root / "docs" / "core_contracts_principles.md",
        root / "docs" / "testing_strategy.md",
    ]

    for path in expected:
        assert path.exists(), f"Missing required file: {path}"


def test_expected_package_dirs_exist() -> None:
    root = Path(__file__).resolve().parents[1]

    expected_dirs = [
        root / "src" / "smartmoneybot",
        root / "src" / "smartmoneybot" / "governance",
        root / "src" / "smartmoneybot" / "core",
        root / "src" / "smartmoneybot" / "discovery",
        root / "src" / "smartmoneybot" / "adapters",
        root / "src" / "smartmoneybot" / "reporting",
        root / "src" / "smartmoneybot" / "ai",
        root / "tests",
        root / "fixtures",
        root / "scripts",
    ]

    for path in expected_dirs:
        assert path.exists(), f"Missing required directory: {path}"
        assert path.is_dir(), f"Expected directory but found non-directory: {path}"
'@

Write-Step "Writing helper scripts"

Write-TextFile -Path (Join-Path $RootPath "scripts\run_tests.ps1") -Content @'
param(
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"

if ($VerboseOutput) {
    python -m pytest -vv
}
else {
    python -m pytest
}
'@

Write-TextFile -Path (Join-Path $RootPath "scripts\bootstrap_dev.ps1") -Content @'
$ErrorActionPreference = "Stop"

python -m pip install --upgrade pip
python -m pip install -e .[dev]
python -m pytest
'@

Write-Step "Writing slice note"

Write-TextFile -Path (Join-Path $RootPath "docs\slice_0_2_notes.md") -Content @'
# Slice 0.2 Notes

Status: Installed

## Goal

Create the minimal Python project skeleton for smartmoneybotv3.

## Files Added

- pyproject.toml
- pytest.ini
- src/smartmoneybot/__init__.py
- src/smartmoneybot/governance/__init__.py
- src/smartmoneybot/core/__init__.py
- src/smartmoneybot/discovery/__init__.py
- src/smartmoneybot/adapters/__init__.py
- src/smartmoneybot/reporting/__init__.py
- src/smartmoneybot/ai/__init__.py
- tests/test_smoke_import.py
- tests/test_project_structure.py
- scripts/run_tests.ps1
- scripts/bootstrap_dev.ps1

## Acceptance Criteria

- Package import works.
- Version import works.
- pytest discovers tests.
- Foundation docs exist.
- Expected package directories exist.
- No domain logic implemented yet.
- No live network needed.

## Out Of Scope

- Domain contracts.
- Serialization.
- Core candle logic.
- Discovery logic.
- Adapters.
- Reporting models.
- AI implementation.
'@

Write-Step "Slice 0.2 installation complete"
Write-Host ""
Write-Host "Next commands:" -ForegroundColor White
Write-Host "  python -m pip install --upgrade pip" -ForegroundColor Green
Write-Host "  python -m pip install -e .[dev]" -ForegroundColor Green
Write-Host "  python -m pytest" -ForegroundColor Green
Write-Host ""
Write-Host "Or use:" -ForegroundColor White
Write-Host "  .\scripts\bootstrap_dev.ps1" -ForegroundColor Green
