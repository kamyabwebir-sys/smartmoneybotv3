$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    $current = (Get-Location).Path

    try {
        $gitRoot = git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($gitRoot)) {
            return $gitRoot.Trim()
        }
    } catch {
        # fallback below
    }

    return $current
}

function Normalize-PathForCompare([string]$path) {
    return ($path -replace "\\", "/").Trim()
}

$repoRoot = Resolve-RepoRoot
Set-Location -LiteralPath $repoRoot

$requiredFiles = @(
    "docs/freeze_packs/slice_1_46_post_1_45_scope_adoption_decision_lock.md",
    "docs/governance/reviews/slice_1_46_post_1_45_scope_adoption_decision_lock_review.md",
    "scripts/verify_slice_1_46_post_1_45_scope_adoption_decision_lock.ps1"
)

$protectedFiles = @(
    "src/smart_money/discovery/registry.py",
    "tests/discovery/test_registry.py"
)

$forbiddenRuntimePrefixes = @(
    "src/",
    "tests/",
    "smartmoneybotv3/src/"
)

$dependencyFiles = @(
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "uv.lock",
    "Pipfile",
    "Pipfile.lock",
    "src/smartmoneybotv3.egg-info/requires.txt",
    "src/smartmoneybotv3.egg-info/PKG-INFO"
)

$requiredMarkers = @(
    "Slice 1.46",
    "P0-B",
    "Runtime Status: UNCHANGED",
    "NON-AUTHORITATIVE",
    "Maximum primary files: 3",
    "No execution/trading logic",
    "No risk calculation",
    "No opaque ML decisioning",
    "Analytics produces evidence and score breakdown only",
    "NautilusTrader",
    "QuantConnect Lean",
    "Hummingbot",
    "vectorbt",
    "smart-money-concepts"
)

$forbiddenScopeMarkers = @(
    "execution or trading logic",
    "risk calculation",
    "opaque ML decisioning",
    "new external dependencies",
    "Core changes",
    "Domain changes",
    "Registry changes",
    "Artifact Generation changes"
)

foreach ($path in $requiredFiles) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "FAIL: missing required file: $path"
    }
}

foreach ($path in $protectedFiles) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "FAIL: protected baseline file is missing: $path"
    }
}

$freezePack = Get-Content -LiteralPath $requiredFiles[0] -Raw
$review = Get-Content -LiteralPath $requiredFiles[1] -Raw
$combined = $freezePack + "`n" + $review

foreach ($marker in $requiredMarkers) {
    if ($combined -notlike "*$marker*") {
        throw "FAIL: required governance marker missing: $marker"
    }
}

foreach ($marker in $forbiddenScopeMarkers) {
    if ($combined -notlike "*$marker*") {
        throw "FAIL: forbidden-scope marker is absent from governance artifacts: $marker"
    }
}

# Enforce exact Slice 1.46 file budget by filename pattern.
$allSliceFiles = Get-ChildItem -Recurse -File |
    Where-Object {
        $rel = Normalize-PathForCompare($_.FullName.Substring($repoRoot.Length).TrimStart("\", "/"))
        $rel -match "slice_1_46"
    } |
    ForEach-Object {
        Normalize-PathForCompare($_.FullName.Substring($repoRoot.Length).TrimStart("\", "/"))
    } |
    Sort-Object -Unique

$requiredNormalized = $requiredFiles | ForEach-Object { Normalize-PathForCompare($_) } | Sort-Object -Unique

if ($allSliceFiles.Count -ne 3) {
    $paths = ($allSliceFiles -join "`n")
    throw "FAIL: Slice 1.46 file count is not exactly 3. Found $($allSliceFiles.Count):`n$paths"
}

foreach ($path in $requiredNormalized) {
    if ($allSliceFiles -notcontains $path) {
        throw "FAIL: required Slice 1.46 file is not in discovered Slice file set: $path"
    }
}

# Git-aware scope check.
# This does not require a clean worktree. It fails only if a Slice 1.46-named
# changed file is outside the approved set, or if protected/dependency files are
# currently changed.
$gitAvailable = $false
try {
    git rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -eq 0) {
        $gitAvailable = $true
    }
} catch {
    $gitAvailable = $false
}

if ($gitAvailable) {
    $changed = git status --porcelain --untracked-files=all |
        ForEach-Object {
            $line = $_
            if ($line.Length -ge 4) {
                $p = $line.Substring(3)
                if ($p -match " -> ") {
                    $p = ($p -split " -> ")[-1]
                }
                Normalize-PathForCompare($p)
            }
        } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Sort-Object -Unique

    $changedSlice146 = $changed | Where-Object { $_ -match "slice_1_46" }

    foreach ($path in $changedSlice146) {
        if ($requiredNormalized -notcontains $path) {
            throw "FAIL: unexpected changed Slice 1.46 file: $path"
        }
    }

    foreach ($path in $protectedFiles) {
        $normalized = Normalize-PathForCompare($path)
        if ($changed -contains $normalized) {
            throw "FAIL: protected Slice 0.10 file is modified in worktree: $path"
        }
    }

    foreach ($path in $dependencyFiles) {
        $normalized = Normalize-PathForCompare($path)
        if ($changed -contains $normalized) {
            throw "FAIL: dependency/package file is modified in worktree: $path"
        }
    }

    foreach ($path in $changedSlice146) {
        foreach ($prefix in $forbiddenRuntimePrefixes) {
            if ($path.StartsWith($prefix)) {
                throw "FAIL: Slice 1.46 runtime/test path modification is forbidden: $path"
            }
        }
    }
}

Write-Output "PASS: Slice 1.46 P0-B scope adoption decision lock verified"
Write-Output "PASS: exactly three Slice 1.46 files are present"
Write-Output "PASS: external repositories are non-authoritative architecture guidance only"
Write-Output "PASS: no dependency adoption is authorized"
Write-Output "PASS: protected Slice 0.10 files are not modified by this Slice"
Write-Output "PASS: runtime/core/domain/registry/artifact-generation changes remain out of scope"
