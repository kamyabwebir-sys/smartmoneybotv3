from smart_money.application.pattern_discovery import extract_wallet_behavior_pattern
from smart_money.application.pattern_governance import PatternPersistenceStore, propose_pattern, rank_pattern_candidates, verify_pattern_store

def test_pattern_governance(tmp_path) -> None:
    pattern=extract_wallet_behavior_pattern("w",features=("early_entry",),source_id="test")
    store=PatternPersistenceStore(tmp_path/"patterns.json")
    store.save(pattern)
    assert verify_pattern_store(pattern,store).matches
    assert propose_pattern(pattern,"repeatable observation").proposal_id
    assert rank_pattern_candidates((pattern,))[0].rank==1
