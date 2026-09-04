from smart_money.application.cross_intelligence import (
    CrossIntelligenceEvidenceProjection,
    bind_cross_subject,
    verify_cross_intelligence_replay,
)
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.domain.wallet_intelligence import WalletIntelligenceObservation
from smart_money.application.token_safety_candidate_binding import TokenSafetyCandidateBinding
from smart_money.core.ids import deterministic_id

def test_cross_intelligence_projection_and_replay() -> None:
    ci={"activity_count":1,"buy_count":1,"data_completeness_bps":9000,"distinct_token_count":1,"native_delta_total":0,"observed_from_slot":1,"observed_to_slot":1,"schema_version":"wallet_intelligence_observation.v1","sell_count":0,"token_delta_total":1,"unknown_count":0,"wallet":"w"}
    wallet=WalletIntelligenceObservation(**ci, observation_id=deterministic_id("wallet_intelligence_observation",ci))
    candidate_id=deterministic_id("solana_wallet_token_candidate",{"activity_count":1,"buy_count":1,"first_slot":1,"last_slot":1,"mint":"t","reasons":("r",),"schema_version":"solana_wallet_token_candidate.v1","wallet":"w"})
    candidate=SolanaWalletTokenCandidate("w","t",1,1,1,1,("r",),candidate_id)
    si={"candidate_id":candidate_id,"freeze_authority":None,"holder_concentration_bps":1,"liquidity_amount":1,"mint_authority":None,"schema_version":"token_safety_candidate_binding.v1","token":"t","token_observation_id":"o","update_authority":None,"wallet":"w"}
    safety=TokenSafetyCandidateBinding(**si,binding_id=deterministic_id("token_safety_candidate_binding",si))
    contract = bind_cross_subject(candidate, wallet, safety)
    projection = CrossIntelligenceEvidenceProjection.from_contract(contract)
    assert verify_cross_intelligence_replay(contract,projection).matches
