from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_candidate_discovery import discover_solana_wallet_token_candidates
from smart_money.application.solana_swap_evidence import extract_solana_swap_evidence
from smart_money.application.solana_wallet_token_activity import build_solana_wallet_token_activity
from smart_money.application.solana_wallet_token_activity_ledger import ingest_solana_wallet_token_activity
from smart_money.domain.solana_observation import SolanaChainObservation


def test_candidate_discovery_returns_explainable_candidate():
    raw = {"transaction": {"signatures": ["sig"]}, "meta": {
        "preBalances": [100], "postBalances": [90],
        "preTokenBalances": [{"accountIndex": 1, "mint": "M", "owner": "W", "uiTokenAmount": {"amount": "0", "decimals": 0}}],
        "postTokenBalances": [{"accountIndex": 1, "mint": "M", "owner": "W", "uiTokenAmount": {"amount": "2", "decimals": 0}}]}}
    observation = SolanaChainObservation(slot=9, observed_at=1, transaction_signature="sig", program_id="p", subject="p")
    activity = build_solana_wallet_token_activity(observation, extract_solana_swap_evidence(raw, owner="W", mint="M"))
    ledger = EvidenceGroundingLedger()
    ingest_solana_wallet_token_activity(activity, ledger)
    candidates = discover_solana_wallet_token_candidates(ledger)
    assert len(candidates) == 1
    assert candidates[0].buy_count == 1
    assert candidates[0].reasons
