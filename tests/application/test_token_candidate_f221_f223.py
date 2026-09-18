from smart_money.application.token_candidate_binding import bind_token_candidate
from smart_money.application.token_candidate_ledger_projection import TokenCandidateLedgerProjection
from smart_money.application.token_candidate_read_model import build_token_candidate_read_model
from smart_money.application.token_candidate_replay import verify_token_candidate_replay
from smart_money.application.token_lifecycle import TokenLifecycleState, build_token_lifecycle

def test_candidate_projection_replay_and_read_model() -> None:
    lifecycle = build_token_lifecycle("t", TokenLifecycleState.CREATED, 1, ("e",))
    binding = bind_token_candidate("t", (lifecycle,))
    projection = TokenCandidateLedgerProjection.from_binding(binding)
    assert verify_token_candidate_replay(binding, projection).replay_matches
    model = build_token_candidate_read_model((binding,))
    assert model.rows[0].candidate_id == binding.candidate_id
