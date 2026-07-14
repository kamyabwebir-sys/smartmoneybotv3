from pathlib import Path


def test_contract_shape_docs_exist() -> None:
    root = Path(__file__).resolve().parents[1]

    expected = [
        root / "docs" / "core_contract_shape_v1.md",
        root / "docs" / "slice_0_4_notes.md",
    ]

    for path in expected:
        assert path.exists(), f"Missing Slice 0.4 doc: {path}"