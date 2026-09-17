import json

from smart_money.application.mainnet_replay import dashboard_shadow_read, replay_transaction_fixture
from smart_money.ingestion.ledger import EvidenceGroundingLedger


def test_mainnet_fixture_replay_and_shadow_read(tmp_path):
    path = tmp_path / "tx.json"
    path.write_text(json.dumps({"result": {"slot": 9, "signature": "sig", "transaction": {"message": {"instructions": []}}}}), encoding="utf-8")
    ledger = EvidenceGroundingLedger()
    assert replay_transaction_fixture(path, ledger)
    read = dashboard_shadow_read(ledger)
    assert read["read_only"] is True and read["evidence_count"] == 1
