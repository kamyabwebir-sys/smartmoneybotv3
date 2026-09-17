from smart_money.application.production_orchestrator import evaluate_production, run_shadow_session


def test_shadow_orchestrator_and_gate():
    rows = run_shadow_session(lambda slot: {"slot": slot}, 100, batches=2, batch_size=2)
    assert [row["slot"] for row in rows] == [100, 101, 102, 103]
    assert evaluate_production(processed=4, failures=0, recovery_ok=True).ready
