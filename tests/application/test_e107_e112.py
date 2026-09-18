from smart_money.application.solana_rpc_production import (
    PersistentCursorRunner, build_retry_execution_evidence, classify_rpc_error,
    fetch_live_transaction,
)

def test_rpc_production_hardening(tmp_path) -> None:
    assert classify_rpc_error({"code": 429}) == "RATE_LIMIT"
    assert build_retry_execution_evidence("rpc", retry_count=1, error_class="RATE_LIMIT").evidence_id
    runner=PersistentCursorRunner(tmp_path/"cursor.json",1)
    assert runner.run_once(lambda cursor: {"slot":cursor+1})["slot"] == 2
    assert fetch_live_transaction("sig",2,{"result":"ok"}).fetch_id
