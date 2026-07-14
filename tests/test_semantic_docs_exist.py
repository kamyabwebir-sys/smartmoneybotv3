from pathlib import Path


def test_semantic_docs_exist() -> None:
    root = Path(__file__).resolve().parents[1]

    expected = [
        root / "docs" / "core_contract_semantics_v1.md",
        root / "docs" / "reason_codes_seed_v1.md",
        root / "docs" / "evidence_policy_v1.md",
        root / "docs" / "deterministic_assumptions_v1.md",
        root / "docs" / "slice_0_3_notes.md",
    ]

    for path in expected:
        assert path.exists(), f"Missing semantic doc: {path}"
