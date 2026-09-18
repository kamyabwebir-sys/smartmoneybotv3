from smart_money.application.live_discovery import (
    LiveDiscoveryDashboardReadModel, LiveDiscoveryReplaySession, build_live_candidate_payload,
    checkpoint_session, ingest_live_activity, poll_solana_boundary, start_live_session,
)
from smart_money.core.ids import deterministic_id

def test_live_discovery_boundary_and_replay() -> None:
    session = start_live_session("solana-rpc", 1)
    checkpoint = checkpoint_session(session, 2)
    assert poll_solana_boundary(lambda cursor: {"slot": cursor + 1}, 2)["slot"] == 3
    wallet = ingest_live_activity("wallet_activity", {"wallet":"w"}, 2)
    token = ingest_live_activity("token_discovery", {"token":"t"}, 2)
    candidate = build_live_candidate_payload({"candidate_id":"c"}, 2)
    replay_id = deterministic_id("live_discovery_replay", {"checkpoint_ids":(checkpoint.checkpoint_id,), "schema_version":"live_discovery_replay.v1", "session_id":session.session_id})
    replay = LiveDiscoveryReplaySession(session.session_id, (checkpoint.checkpoint_id,), replay_id)
    model = LiveDiscoveryDashboardReadModel(session, (checkpoint,), (wallet, token, candidate))
    assert replay.replay_id and len(model.candidates) == 3
