import json
from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.provider_adapters import SolanaRPCObservationAdapter, normalize_provider_payload
from smart_money.application.provider_runtime import (
    build_provider_health_evidence, ingest_provider_payload, load_solana_rpc_fixture,
    resolve_provider_consensus, verify_provider_replay,
)

def test_provider_runtime_pipeline(tmp_path) -> None:
    fixture = tmp_path / "rpc.json"
    fixture.write_text(json.dumps([{"slot": 1, "value": "x"}]), encoding="utf-8")
    raw = load_solana_rpc_fixture(fixture)[0]
    adapter = SolanaRPCObservationAdapter()
    payload = normalize_provider_payload(adapter, raw)
    ledger = EvidenceGroundingLedger()
    assert ingest_provider_payload(adapter, raw, ledger).evidence_id
    assert verify_provider_replay(adapter, raw, payload).matches
    assert resolve_provider_consensus("t", (("a", "x"), ("b", "x"))).conflicted is False
    assert build_provider_health_evidence("rpc", observed_at=1, fresh=True).fresh
