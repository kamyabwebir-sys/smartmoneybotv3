from smart_money.application.cross_intelligence_ranking_query import query_cross_intelligence_ranking
from smart_money.application.cross_intelligence_ranking_audit import audit_cross_intelligence_ranking
from smart_money.application.cross_intelligence_ranking_store import CrossIntelligenceRankingStore

def test_empty_ranking_query_audit_store(tmp_path) -> None:
    result = query_cross_intelligence_ranking(())
    receipt = audit_cross_intelligence_ranking(result)
    store = CrossIntelligenceRankingStore(tmp_path / "ranking.json")
    store.save(result)
    assert receipt.result_count == 0
    assert store.get(result.query_id) == result
