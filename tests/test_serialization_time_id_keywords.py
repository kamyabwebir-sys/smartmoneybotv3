from pathlib import Path


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