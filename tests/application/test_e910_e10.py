from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.live_discovery import (
    CheckpointStore, LiveSessionStore, ProviderRetryPolicy,
    SolanaProductionConnector, bind_live_evidence, checkpoint_session,
    ingest_live_activity, start_live_session, verify_checkpoint_recovery,
    verify_live_candidate_replay,
)


def test_live_hardening_and_connector(tmp_path) -> None:
    session = start_live_session("rpc", 1)
    ss = LiveSessionStore(tmp_path / "s.json")
    ss.save(session)
    cp = checkpoint_session(session, 2)
    cs = CheckpointStore(tmp_path / "c.json")
    cs.save(cp)
    assert verify_checkpoint_recovery(cp, cs)
    payload = ingest_live_activity("wallet_activity", {"wallet": "w"}, 2)
    assert bind_live_evidence(EvidenceGroundingLedger(), payload)
    assert verify_live_candidate_replay(payload, payload)
    assert SolanaProductionConnector().fetch(lambda x: {"slot": x + 1}, 2)["slot"] == 3
    assert ProviderRetryPolicy(2, 1).max_retries == 2
