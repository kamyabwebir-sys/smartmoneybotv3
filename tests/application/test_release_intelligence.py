from smart_money.application.release_intelligence import (
    build_token_safety_production_profile,
    build_evidence_conflict_surface,
    build_historical_performance_surface,
    build_persian_analyst_dashboard,
    build_release_audit_chain,
    evaluate_production_intelligence_release,
    explain_opportunity_in_persian,
    rank_wallet_token_opportunities,
    verify_release_replay,
)


def test_release_profiles_ranking_and_persian_explanation() -> None:
    profile = build_token_safety_production_profile("token-1", "summary-1", 10, 2)
    assert profile.safety_score_bps == 8000
    ranked = rank_wallet_token_opportunities((
        {"subject_id": "a", "wallet": "w1", "token": "t1", "wallet_score_bps": 9000, "token_safety_bps": 7000},
        {"subject_id": "b", "wallet": "w2", "token": "t2", "wallet_score_bps": 8000, "token_safety_bps": 8000},
    ))
    assert [item.subject_id for item in ranked] == ["a", "b"]
    explanation = explain_opportunity_in_persian(ranked[0])
    assert "Evidence" in explanation.text
    assert explanation == explain_opportunity_in_persian(ranked[0])


def test_conflict_performance_and_dashboard_are_replay_stable() -> None:
    ranked = rank_wallet_token_opportunities((
        {"subject_id": "a", "wallet": "w1", "token": "t1", "wallet_score_bps": 9000, "token_safety_bps": 7000},
    ))
    conflict = build_evidence_conflict_surface(
        "a", ({"code": "IDENTITY_MISMATCH", "blocking": True},)
    )
    performance = build_historical_performance_surface(
        "a", validated_count=8, failed_count=2, calibration_error_bps=500
    )
    dashboard = build_persian_analyst_dashboard(
        ranked, (conflict,), (performance,)
    )
    assert dashboard.blocked_subject_ids == ("a",)
    assert performance.success_rate_bps == 8000
    assert dashboard == build_persian_analyst_dashboard(
        ranked, (conflict,), (performance,)
    )


def test_audit_chain_replay_and_release_gate_fail_closed() -> None:
    ranked = rank_wallet_token_opportunities((
        {"subject_id": "a", "wallet": "w1", "token": "t1", "wallet_score_bps": 9000, "token_safety_bps": 8000},
    ))
    performance = build_historical_performance_surface(
        "a", validated_count=9, failed_count=1, calibration_error_bps=400
    )
    dashboard = build_persian_analyst_dashboard(ranked, (), (performance,))
    chain = build_release_audit_chain(dashboard)
    assert all(
        entry.previous_entry_id == chain.entries[index - 1].entry_id
        for index, entry in enumerate(chain.entries[1:], start=1)
    )
    replay = verify_release_replay(dashboard, chain)
    assert replay.matches
    gate = evaluate_production_intelligence_release(dashboard, chain, replay)
    assert gate.ready
    assert gate.passed_checks == gate.checks

    conflict = build_evidence_conflict_surface(
        "a", ({"code": "IDENTITY_MISMATCH", "blocking": True},)
    )
    blocked_dashboard = build_persian_analyst_dashboard(
        ranked, (conflict,), (performance,)
    )
    blocked_chain = build_release_audit_chain(blocked_dashboard)
    blocked_replay = verify_release_replay(blocked_dashboard, blocked_chain)
    blocked_gate = evaluate_production_intelligence_release(
        blocked_dashboard, blocked_chain, blocked_replay
    )
    assert not blocked_gate.ready
    assert "no_blocking_conflicts" not in blocked_gate.passed_checks
