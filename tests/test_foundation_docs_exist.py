from pathlib import Path


def test_foundation_docs_exist() -> None:
    root = Path(__file__).resolve().parents[1]

    expected = [
        root / "README.md",
        root / "fixtures",
        root / "docs" / "build_plan.md",
        root / "docs" / "scope_guardrails.md",
        root / "docs" / "architecture_boundaries.md",
        root / "docs" / "open_questions.md",
        root / "docs" / "core_contracts_principles.md",
        root / "docs" / "testing_strategy.md",
    ]

    for path in expected:
        assert path.exists(), f"Missing foundation path: {path}"
