"""Behavioral contract: documentation exists and contains required content.

Replaces:
  test_contract_shape_docs_exist, test_foundation_docs_exist,
  test_semantic_docs_exist, test_serialization_time_id_docs_exist,
  test_project_structure (doc部分), test_contract_shape_keywords,
  test_foundation_keywords, test_semantic_keywords,
  test_serialization_time_id_keywords
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


# ── Doc existence ────────────────────────────────────────────────────────────

REQUIRED_DOCS: list[Path] = [
    DOCS / "core_contract_shape_v1.md",
    DOCS / "slice_0_4_notes.md",
    DOCS / "build_plan.md",
    DOCS / "scope_guardrails.md",
    DOCS / "architecture_boundaries.md",
    DOCS / "open_questions.md",
    DOCS / "core_contracts_principles.md",
    DOCS / "testing_strategy.md",
    DOCS / "core_contract_semantics_v1.md",
    DOCS / "reason_codes_seed_v1.md",
    DOCS / "evidence_policy_v1.md",
    DOCS / "deterministic_assumptions_v1.md",
    DOCS / "slice_0_3_notes.md",
    DOCS / "serialization_time_id_semantics_v1.md",
    DOCS / "slice_0_5_notes.md",
    ROOT / "README.md",
    ROOT / "fixtures",
]


@pytest.mark.parametrize("path", REQUIRED_DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_required_doc_exists(path: Path) -> None:
    assert path.exists(), f"Missing required path: {path}"


# ── Required package directories ─────────────────────────────────────────────

REQUIRED_DIRS: list[Path] = [
    ROOT / "src" / "smartmoneybot",
    ROOT / "src" / "smartmoneybot" / "governance",
    ROOT / "src" / "smartmoneybot" / "core",
    ROOT / "src" / "smartmoneybot" / "discovery",
    ROOT / "src" / "smartmoneybot" / "adapters",
    ROOT / "src" / "smartmoneybot" / "reporting",
    ROOT / "src" / "smartmoneybot" / "ai",
    ROOT / "tests",
    ROOT / "fixtures",
    ROOT / "scripts",
]


@pytest.mark.parametrize("path", REQUIRED_DIRS, ids=lambda p: str(p.relative_to(ROOT)))
def test_required_dir_exists(path: Path) -> None:
    assert path.is_dir(), f"Missing required directory: {path}"


# ── Keyword contracts per document ───────────────────────────────────────────
# Each entry: (doc_path, required_terms_or_phrases)

DOC_KEYWORDS: list[tuple[Path, list[str]]] = [
    # core_contract_shape_v1.md
    (
        DOCS / "core_contract_shape_v1.md",
        [
            "Status: Proposed Freeze for Slice 0.4",
            "documentation-only",
            "Core constructors must never read wall-clock time implicitly",
            "created_at must be supplied explicitly",
            "schema_version",
            "contract_type",
            "deterministic ID inputs",
            "canonical serialization",
            "Unresolved Freeze Gates Before Python Models",
        ],
    ),
    # build_plan.md
    (
        DOCS / "build_plan.md",
        [
            "Candles -> Structure/Context -> Setup -> Decision -> Alert",
            "deterministic",
            "replayable",
            "contracts before engines",
            "strict core boundaries",
        ],
    ),
    # scope_guardrails.md
    (
        DOCS / "scope_guardrails.md",
        [
            "trade execution",
            "broker side effects",
            "portfolio management",
            "ML-driven truth generation",
            "canonical serialization",
        ],
    ),
    # core_contract_semantics_v1.md
    (
        DOCS / "core_contract_semantics_v1.md",
        [
            "Candle",
            "Market",
            "Symbol",
            "Timeframe",
            "Structure",
            "Swing High",
            "Swing Low",
            "BOS",
            "CHOCH",
            "Sweep",
            "Liquidity",
            "Liquidity Zone",
            "Displacement",
            "Imbalance",
            "FVG",
            "Context",
            "Setup Candidate",
            "Decision",
            "Alert",
            "Evidence Item",
            "Reason Code",
            "Risk Flag",
            "Token Candidate",
            "Wallet Profile",
            "Suspicious Cluster",
            "Pump/Dump-like Anomaly",
            "Deterministic Replay",
            "AI Role Boundary",
        ],
    ),
    # reason_codes_seed_v1.md
    (
        DOCS / "reason_codes_seed_v1.md",
        [
            "STRUCTURE_BOS_BULL",
            "STRUCTURE_CHOCH_BEAR",
            "CONTEXT_AT_FVG",
            "SETUP_CANDIDATE_VALID",
            "DECISION_DEFER",
            "RISK_SUSPICIOUS_CLUSTER",
        ],
    ),
    # evidence_policy_v1.md (case-insensitive check done separately)
    # deterministic_assumptions_v1.md
    (
        DOCS / "deterministic_assumptions_v1.md",
        [
            "closed candles",
            "ascending",
            "no network dependency",
            "same outputs",
            "Mutable global state is disallowed",
        ],
    ),
    # serialization_time_id_semantics_v1.md
    (
        DOCS / "serialization_time_id_semantics_v1.md",
        [
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
        ],
    ),
]


def _doc_id(path: Path) -> str:
    return str(path.relative_to(DOCS))


@pytest.mark.parametrize(
    "doc_path,terms",
    DOC_KEYWORDS,
    ids=[_doc_id(p) for p, _ in DOC_KEYWORDS],
)
def test_doc_contains_required_terms(doc_path: Path, terms: list[str]) -> None:
    content = doc_path.read_text(encoding="utf-8")
    for term in terms:
        assert term in content, f"Missing term in {doc_path.name}: {term!r}"


# ── Special-case keyword checks ──────────────────────────────────────────────

def test_evidence_policy_mentions_determinism_and_ai() -> None:
    content = (DOCS / "evidence_policy_v1.md").read_text(encoding="utf-8")
    assert "deterministic" in content.lower()
    assert "AI" in content


def test_contract_shape_code_fence_count() -> None:
    content = (DOCS / "core_contract_shape_v1.md").read_text(encoding="utf-8")
    assert content.count("```python") == 3
    assert content.count("```") == 6


def test_slice_0_5_has_no_python_contracts() -> None:
    assert not (ROOT / "src" / "smartmoney" / "core" / "contracts").exists()
