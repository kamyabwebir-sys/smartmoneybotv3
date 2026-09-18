from smart_money.application.token_safety_evidence_summary import TokenSafetyEvidenceSummary
from smart_money.application.token_safety_summary_store import TokenSafetySummaryStore
from smart_money.application.token_safety_summary_store_replay import verify_token_safety_summary_store
from smart_money.core.ids import deterministic_id

def test_summary_store_and_replay(tmp_path) -> None:
    identity = {"observation_id":"o","schema_version":"token_safety_evidence_summary.v1","total_rules":1,
                "triggered_reasons":(), "triggered_rule_ids":(), "triggered_rules":0}
    summary = TokenSafetyEvidenceSummary("o", 1, 0, (), (), deterministic_id("token_safety_evidence_summary", identity))
    store = TokenSafetySummaryStore(tmp_path / "summary.json")
    store.save(summary)
    assert verify_token_safety_summary_store(summary, store).matches
