from smart_money.application.cross_intelligence_ledger import ingest_cross_intelligence
from smart_money.application.cross_intelligence import bind_cross_subject
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.domain.wallet_intelligence import WalletIntelligenceObservation
from smart_money.application.token_safety_candidate_binding import TokenSafetyCandidateBinding
from smart_money.core.ids import deterministic_id
from smart_money.application.cross_intelligence_store import CrossIntelligenceStore
from smart_money.application.cross_intelligence_read_model import build_cross_intelligence_read_model, query_cross_intelligence
from smart_money.application.cross_intelligence_ranking import rank_cross_intelligence
from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger

def test_cross_intelligence_pipeline(tmp_path) -> None:
    wi={"activity_count":1,"buy_count":1,"data_completeness_bps":1,"distinct_token_count":1,"native_delta_total":0,"observed_from_slot":1,"observed_to_slot":1,"schema_version":"wallet_intelligence_observation.v1","sell_count":0,"token_delta_total":1,"unknown_count":0,"wallet":"w"}
    wallet=WalletIntelligenceObservation(**wi, observation_id=deterministic_id("wallet_intelligence_observation",wi))
    ci={"activity_count":1,"buy_count":1,"first_slot":1,"last_slot":1,"mint":"t","reasons":("r",),"schema_version":"solana_wallet_token_candidate.v1","wallet":"w"}
    candidate=SolanaWalletTokenCandidate(**ci,candidate_id=deterministic_id("solana_wallet_token_candidate",ci))
    si={"candidate_id":candidate.candidate_id,"freeze_authority":None,"holder_concentration_bps":1,"liquidity_amount":1,"mint_authority":None,"schema_version":"token_safety_candidate_binding.v1","token":"t","token_observation_id":"o","update_authority":None,"wallet":"w"}
    safety=TokenSafetyCandidateBinding(**si,binding_id=deterministic_id("token_safety_candidate_binding",si))
    cross_contract=bind_cross_subject(candidate,wallet,safety)
    ledger = EvidenceGroundingLedger()
    receipt = ingest_cross_intelligence(cross_contract, ledger)
    store = CrossIntelligenceStore(tmp_path / "cross.json")
    store.save(cross_contract)
    model = build_cross_intelligence_read_model((cross_contract,))
    assert receipt.evidence_id and store.get(cross_contract.cross_id) == cross_contract
    assert len(query_cross_intelligence(model, wallet=cross_contract.wallet)) == 1
    assert rank_cross_intelligence((cross_contract,))[0].rank == 1
