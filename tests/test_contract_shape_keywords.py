from pathlib import Path


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

    assert content.count("```python") == 3
    assert content.count("```") == 6