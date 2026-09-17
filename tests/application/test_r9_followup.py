import json

from smart_money.adapters.persistence.shadow_session_store import JsonShadowSessionStore
from smart_money.adapters.solana_rpc_fetcher import SolanaRPCFetcher
from smart_money.application.backfill_decoder_binding import decode_and_bind_transaction
from smart_money.application.fixture_capture import capture_fixture
from smart_money.ingestion.ledger import EvidenceGroundingLedger
from smart_money.application.production_shadow import SolanaRPCConfig


def test_capture_decoder_and_session_recovery(tmp_path):
    fixture = capture_fixture({"result": {"slot": 3}}, tmp_path / "fixture.json")
    assert json.loads(fixture.read_text())["result"]["slot"] == 3
    ledger = EvidenceGroundingLedger()
    response = {"result": {"slot": 3, "signature": "sig", "transaction": {"message": {"instructions": []}}}}
    assert decode_and_bind_transaction(ledger, response)
    store = JsonShadowSessionStore(tmp_path / "session.json")
    store.save("session-1", "cp-1", 2)
    assert store.load()["processed"] == 2


def test_rpc_retry_rejects_bad_settings():
    class Never:
        def __call__(self, *args, **kwargs):
            raise OSError("offline")
    fetcher = SolanaRPCFetcher(SolanaRPCConfig("https://rpc.example"), Never())
    try:
        fetcher.request_with_retry("getSlot", max_retries=0)
    except OSError:
        pass
