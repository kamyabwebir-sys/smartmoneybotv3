from smart_money.application.pattern_discovery import (
    PatternEvidenceProjection, PatternKind, audit_pattern_query,
    bind_patterns, extract_token_discovery_pattern, extract_wallet_behavior_pattern,
    query_patterns, verify_pattern_replay,
)

def test_pattern_discovery_binding_projection_replay_query_audit() -> None:
    wallet=extract_wallet_behavior_pattern("w",features=("early_entry","holding_consistency"),source_id="test")
    token=extract_token_discovery_pattern("t",features=("liquidity_survival",),source_id="test")
    binding=bind_patterns(wallet,token)
    projection=PatternEvidenceProjection.from_binding(binding)
    found=query_patterns((wallet,token),kind=PatternKind.WALLET_BEHAVIOR)
    audit=audit_pattern_query(found)
    assert verify_pattern_replay(binding,projection)
    assert len(found)==1 and audit.result_count==1
