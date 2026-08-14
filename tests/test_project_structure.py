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
        root / "src" / "smart_money",
        root / "src" / "smart_money" / "core",
        root / "src" / "smart_money" / "discovery",
        root / "src" / "smart_money" / "ingestion",
        root / "tests",
        root / "fixtures",
        root / "scripts",
    ]

    for path in expected_dirs:
        assert path.exists(), f"Missing required directory: {path}"
        assert path.is_dir(), f"Expected directory but found non-directory: {path}"
