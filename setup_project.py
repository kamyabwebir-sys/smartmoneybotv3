import os
from pathlib import Path

files = {
    "tests/test_contract_shape_docs_exist.py": """from pathlib import Path

def test_contract_shape_docs_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    expected = [
        root / "docs" / "core_contract_shape_v1.md",
        root / "docs" / "slice_0_4_notes.md",
    ]
    for path in expected:
        assert path.exists(), f"Missing Slice 0.4 doc: {path}"
""",
    "tests/test_contract_shape_keywords.py": """from pathlib import Path

def test_contract_shape_governance_terms() -> None:
    root = Path(__file__).resolve().parents[1]
    content = (root / "docs" / "core_contract_shape_v1.md").read_text(encoding="utf-8")
    required = [
        "Status: Proposed Freeze for Slice 0.4",
        "documentation-only",
        "Core constructors must never read wall-clock time implicitly",
        "created_at must be supplied explicitly",
        "schema_version",
        "contract_type",
        "deterministic ID inputs",
        "canonical serialization",
        "Unresolved Freeze Gates Before Python Models",
    ]
    for term in required:
        assert term in content, f"Missing Slice 0.4 term: {term}"

def test_contract_shape_has_three_python_fences() -> None:
    root = Path(__file__).resolve().parents[1]
    content = (root / "docs" / "core_contract_shape_v1.md").read_text(encoding="utf-8")
    assert content.count("
```python") == 3
assert content.count("
```") == 6
""",
    "tests/test_serialization_time_id_docs_exist.py": """from pathlib import Path

def test_serialization_time_id_docs_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    expected = [
        root / "docs" / "serialization_time_id_semantics_v1.md",
        root / "docs" / "slice_0_5_notes.md",
    ]
    for path in expected:
        assert path.exists(), f"Missing Slice 0.5 doc: {path}"
""",
    "tests/test_serialization_time_id_keywords.py": """from pathlib import Path

def test_serialization_time_id_semantics_terms() -> None:
    root = Path(__file__).resolve().parents[1]
    content = (root / "docs" / "serialization_time_id_semantics_v1.md").read_text(encoding="utf-8")
    required = [
        "Status: Proposed Freeze for Slice 0.5",
        "timezone-aware UTC",
        "YYYY-MM-DDTHH:MM:SS.ffffffZ",
        "wall-clock reads inside core constructors are forbidden",
        "created_at participates in canonical serialization",
        "created_at does not participate in deterministic ID inputs",
        "Decimal values must be represented as canonical strings",
        "Canonical serialization uses lexicographic ordering",
        "Collections must be represented as ordered tuples",
        "Arbitrary mapping payloads are not frozen",
    ]
    for term in required:
        assert term in content, f"Missing Slice 0.5 term: {term}"

def test_slice_0_5_does_not_create_python_contracts() -> None:
    root = Path(__file__).resolve().parents[1]
    assert not (root / "src" / "smartmoney" / "core" / "contracts").exists()
""",
    "scripts/install_slice_0_4.ps1": """param([string]$ProjectRoot = ".", [switch]$Force)
$ErrorActionPreference = "Stop"
$RootPath = (Resolve-Path -LiteralPath $ProjectRoot).Path
New-Item -ItemType Directory -Path (Join-Path $RootPath "docs") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $RootPath "tests") -Force | Out-Null

$content = @"
# Core Contract Shape v1
Status: Proposed Freeze for Slice 0.4
...
"@
Set-Content -Path (Join-Path $RootPath "docs/core_contract_shape_v1.md") -Value $content -Encoding UTF8
Write-Host "Slice 0.4 Installed"
""",
    "scripts/install_slice_0_5.ps1": """param([string]$ProjectRoot = ".", [switch]$Force)
$ErrorActionPreference = "Stop"
$RootPath = (Resolve-Path -LiteralPath $ProjectRoot).Path
New-Item -ItemType Directory -Path (Join-Path $RootPath "docs") -Force | Out-Null

$content = @"
# Serialization, Time, and ID Semantics v1
Status: Proposed Freeze for Slice 0.5
...
"@
Set-Content -Path (Join-Path $RootPath "docs/serialization_time_id_semantics_v1.md") -Value $content -Encoding UTF8
Write-Host "Slice 0.5 Installed"
"""
}

for path, content in files.items():
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {path}")
"""