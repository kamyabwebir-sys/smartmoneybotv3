from pathlib import Path


def _read_doc(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_core_semantic_keywords_present() -> None:
    root = Path(__file__).resolve().parents[1]
    content = _read_doc(root / "docs" / "core_contract_semantics_v1.md")

    required_terms = [
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
    ]

    for term in required_terms:
        assert term in content, f"Missing semantic term: {term}"


def test_reason_code_seed_has_expected_style_examples() -> None:
    root = Path(__file__).resolve().parents[1]
    content = _read_doc(root / "docs" / "reason_codes_seed_v1.md")

    required_codes = [
        "STRUCTURE_BOS_BULL",
        "STRUCTURE_CHOCH_BEAR",
        "CONTEXT_AT_FVG",
        "SETUP_CANDIDATE_VALID",
        "DECISION_DEFER",
        "RISK_SUSPICIOUS_CLUSTER",
    ]

    for code in required_codes:
        assert code in content, f"Missing reason code seed: {code}"


def test_evidence_policy_mentions_determinism_and_ai_boundary() -> None:
    root = Path(__file__).resolve().parents[1]
    content = _read_doc(root / "docs" / "evidence_policy_v1.md")

    assert "deterministic" in content.lower()
    assert "AI" in content


def test_deterministic_assumptions_cover_core_replay_constraints() -> None:
    root = Path(__file__).resolve().parents[1]
    content = _read_doc(root / "docs" / "deterministic_assumptions_v1.md")

    required_phrases = [
        "closed candles",
        "ascending",
        "no network dependency",
        "same outputs",
        "Mutable global state is disallowed",
    ]

    for phrase in required_phrases:
        assert phrase in content, f"Missing deterministic assumption phrase: {phrase}"
