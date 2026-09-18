from smart_money.application.token_candidate_binding import bind_token_candidate
from smart_money.application.token_candidate_safety_projection import TokenCandidateSafetyEvidenceProjection
from smart_money.application.token_lifecycle import TokenLifecycleState, build_token_lifecycle
from smart_money.application.token_safety_evidence_summary import TokenSafetyEvidenceSummary
from smart_money.application.token_safety_summary_input_binding import bind_token_safety_summary_input
from smart_money.application.token_safety_summary_replay_verification import verify_token_safety_summary_replay
from smart_money.core.ids import deterministic_id

def test_safety_summary_binding_projection_replay() -> None:
    lifecycle = build_token_lifecycle("t", TokenLifecycleState.CREATED, 1, ("e",))
    candidate = bind_token_candidate("t", (lifecycle,))
    identity = {"observation_id":"obs","schema_version":"token_safety_evidence_summary.v1","total_rules":1,
                "triggered_reasons":(), "triggered_rule_ids":(), "triggered_rules":0}
    summary = TokenSafetyEvidenceSummary("obs", 1, 0, (), (), deterministic_id("token_safety_evidence_summary", identity))
    binding = bind_token_safety_summary_input(candidate, summary)
    projection = TokenCandidateSafetyEvidenceProjection.from_binding(binding)
    assert verify_token_safety_summary_replay(binding, projection).matches
