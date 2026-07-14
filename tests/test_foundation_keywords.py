from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_build_plan_pipeline_and_boundaries() -> None:
    root = Path(__file__).resolve().parents[1]
    content = read_text(root / "docs" / "build_plan.md")

    required = [
        "Candles -> Structure/Context -> Setup -> Decision -> Alert",
        "deterministic",
        "replayable",
        "contracts before engines",
        "strict core boundaries",
    ]

    for term in required:
        assert term in content


def test_scope_guardrails_forbid_out_of_core_items() -> None:
    root = Path(__file__).resolve().parents[1]
    content = read_text(root / "docs" / "scope_guardrails.md")

    required = [
        "trade execution",
        "broker side effects",
        "portfolio management",
        "ML-driven truth generation",
        "canonical serialization",
    ]

    for term in required:
        assert term in content
