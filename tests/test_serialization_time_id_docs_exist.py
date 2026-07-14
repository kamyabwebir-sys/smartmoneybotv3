from pathlib import Path


def test_serialization_time_id_docs_exist() -> None:
    root = Path(__file__).resolve().parents[1]

    expected = [
        root / "docs" / "serialization_time_id_semantics_v1.md",
        root / "docs" / "slice_0_5_notes.md",
    ]

    for path in expected:
        assert path.exists(), f"Missing Slice 0.5 doc: {path}"