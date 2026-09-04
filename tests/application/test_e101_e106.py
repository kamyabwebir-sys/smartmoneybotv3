from smart_money.application.solana_rpc_production import (
    ProductionReplayFixture, RateLimitBackoff, build_connector_health,
    normalize_rpc_response, run_cursor_loop,
)
from smart_money.core.ids import deterministic_id


def test_production_connector_boundaries() -> None:
    assert normalize_rpc_response({"result": {"slot": 2}})["result"]["slot"] == 2
    assert RateLimitBackoff(2, 3).delay_slots(2) == 12
    assert run_cursor_loop(lambda slot: {"slot": slot + 1}, 1, steps=2)[-1]["slot"] == 3
    fixture_id = deterministic_id("solana_production_replay_fixture", {
        "requests": ({"method": "getSlot"},), "responses": ({"result": 2},),
        "schema_version": "solana_production_replay_fixture.v1"})
    assert ProductionReplayFixture(({"method": "getSlot"},), ({"result": 2},), fixture_id)
    assert build_connector_health("solana", request_count=2, failure_count=0).evidence_id
