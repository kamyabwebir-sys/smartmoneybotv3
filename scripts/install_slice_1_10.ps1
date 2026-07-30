#requires -Version 7.0
[CmdletBinding()]
param(
    [string] $ProjectRoot = ".",
    [switch] $Apply,
    [switch] $Force,
    [switch] $RunPytest
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info {
    param([Parameter(Mandatory = $true)][string] $Message)
    Write-Host "[slice-1.10] $Message"
}

function Get-FullProjectPath {
    param([Parameter(Mandatory = $true)][string] $Path)
    return [System.IO.Path]::GetFullPath($Path)
}

function Assert-UnderRoot {
    param(
        [Parameter(Mandatory = $true)][string] $Root,
        [Parameter(Mandatory = $true)][string] $Path
    )

    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    )

    $pathFull = [System.IO.Path]::GetFullPath($Path)

    if (-not $pathFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Fail-closed: path escapes project root: $Path"
    }
}

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)][string] $Root,
        [Parameter(Mandatory = $true)][string] $RelativePath
    )

    $full = Join-Path -Path $Root -ChildPath $RelativePath
    Assert-UnderRoot -Root $Root -Path $full

    if (-not (Test-Path -LiteralPath $full)) {
        if ($Apply) {
            New-Item -ItemType Directory -Path $full -Force | Out-Null
            Write-Info "created directory: $RelativePath"
        }
        else {
            Write-Info "would create directory: $RelativePath"
        }
    }
    else {
        Write-Info "directory exists: $RelativePath"
    }
}

function Write-TextFile {
    param(
        [Parameter(Mandatory = $true)][string] $Root,
        [Parameter(Mandatory = $true)][string] $RelativePath,
        [Parameter(Mandatory = $true)][string] $Content
    )

    $path = Join-Path -Path $Root -ChildPath $RelativePath
    Assert-UnderRoot -Root $Root -Path $path

    if ((Test-Path -LiteralPath $path) -and (-not $Force)) {
        Write-Info "exists, skipped: $RelativePath"
        return
    }

    if ($Apply) {
        $parent = Split-Path -Parent $path
        if ($parent -and -not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }

        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($path, $Content, $utf8NoBom)
        Write-Info "wrote: $RelativePath"
    }
    else {
        Write-Info "would write: $RelativePath"
    }
}

$root = Get-FullProjectPath -Path $ProjectRoot
Set-Location $root

Write-Info "project root: $root"

$allowedDirectories = @(
    "tests/discovery",
    "artifacts/discovery/em003"
)

foreach ($dir in $allowedDirectories) {
    Ensure-Directory -Root $root -RelativePath $dir
}

$verifierContent = @"
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_evidence_report() -> dict[str, Any]:
    return {
        "em_id": "EM-003",
        "status": "PARTIAL",
        "approval_status": "NOT_APPROVED",
        "promotion_gate": "LOCKED",
        "implementation_authority": "NONE",
        "deterministic": True,
        "replayable": True,
        "cases": [
            {"id": f"EM003-CASE-{i:03d}", "status": "NOT_EXECUTED"}
            for i in range(1, 11)
        ],
    }


def build_attachment_register() -> dict[str, Any]:
    return {
        "em_id": "EM-003",
        "artifacts": [
            "artifacts/discovery/em003/evidence_report.json",
            "artifacts/discovery/em003/attachment_register.json",
        ],
    }


def write_artifacts(root: Path) -> None:
    out_dir = root / "artifacts" / "discovery" / "em003"
    out_dir.mkdir(parents=True, exist_ok=True)

    report = build_evidence_report()
    register = build_attachment_register()

    (out_dir / "evidence_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    (out_dir / "attachment_register.json").write_text(
        json.dumps(register, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    write_artifacts(Path.cwd())
"@

$testContent = @"
from __future__ import annotations

import importlib.util
from pathlib import Path


def load_verifier_module():
    verifier_path = Path.cwd() / "tests" / "discovery" / "em003_verifier.py"
    spec = importlib.util.spec_from_file_location("em003_verifier", verifier_path)

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_em003_report_is_governance_safe() -> None:
    verifier = load_verifier_module()
    report = verifier.build_evidence_report()

    assert report["em_id"] == "EM-003"
    assert report["status"] == "PARTIAL"
    assert report["approval_status"] == "NOT_APPROVED"
    assert report["promotion_gate"] == "LOCKED"
    assert report["implementation_authority"] == "NONE"
    assert report["deterministic"] is True
    assert report["replayable"] is True


def test_em003_cases_are_deterministic() -> None:
    verifier = load_verifier_module()

    first = verifier.build_evidence_report()
    second = verifier.build_evidence_report()

    assert first == second
    assert len(first["cases"]) == 10
    assert first["cases"][0]["id"] == "EM003-CASE-001"
    assert first["cases"][-1]["id"] == "EM003-CASE-010"


def test_em003_attachment_register_is_scaffold_only() -> None:
    verifier = load_verifier_module()
    register = verifier.build_attachment_register()

    assert register["em_id"] == "EM-003"
    assert register["artifacts"] == [
        "artifacts/discovery/em003/evidence_report.json",
        "artifacts/discovery/em003/attachment_register.json",
    ]
"@

$reportContent = @"
{
  "approval_status": "NOT_APPROVED",
  "cases": [],
  "deterministic": true,
  "em_id": "EM-003",
  "implementation_authority": "NONE",
  "promotion_gate": "LOCKED",
  "replayable": true,
  "status": "PARTIAL"
}
"@

$registerContent = @"
{
  "artifacts": [
    "artifacts/discovery/em003/evidence_report.json",
    "artifacts/discovery/em003/attachment_register.json"
  ],
  "em_id": "EM-003"
}
"@

Write-TextFile -Root $root -RelativePath "tests/discovery/em003_verifier.py" -Content $verifierContent
Write-TextFile -Root $root -RelativePath "tests/discovery/test_em003_verifier.py" -Content $testContent
Write-TextFile -Root $root -RelativePath "artifacts/discovery/em003/evidence_report.json" -Content $reportContent
Write-TextFile -Root $root -RelativePath "artifacts/discovery/em003/attachment_register.json" -Content $registerContent

if ($Apply -and $RunPytest) {
    Write-Info "running pytest for EM-003 verifier only"
    python -m pytest tests/discovery/test_em003_verifier.py -q
}

Write-Info "done"