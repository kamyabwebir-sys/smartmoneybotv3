from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_swap_evidence import extract_solana_swap_evidence
from smart_money.application.solana_wallet_token_activity import build_solana_wallet_token_activity
from smart_money.application.solana_wallet_token_activity_ledger import ingest_solana_wallet_token_activity
from smart_money.application.solana_wallet_token_activity_query import query_solana_wallet_token_activity
from smart_money.domain.solana_observation import SolanaChainObservation


def test_activity_query_filters_and_orders():
    raw = {"transaction": {"signatures": ["sig"]}, "meta": {
        "preBalances": [100], "postBalances": [90],
        "preTokenBalances": [{"accountIndex": 1, "mint": "M", "owner": "W", "uiTokenAmount": {"amount": "0", "decimals": 0}}],
        "postTokenBalances": [{"accountIndex": 1, "mint": "M", "owner": "W", "uiTokenAmount": {"amount": "2", "decimals": 0}}]}}
    obs = SolanaChainObservation(slot=7, observed_at=1, transaction_signature="sig", program_id="p", subject="p")
    activity = build_solana_wallet_token_activity(obs, extract_solana_swap_evidence(raw, owner="W", mint="M"))
    ledger = EvidenceGroundingLedger()
    ingest_solana_wallet_token_activity(activity, ledger)
    result = query_solana_wallet_token_activity(ledger, wallet="W", mint="M", direction="BUY", min_slot=7)
    assert len(result.activities) == 1
    assert result.activities[0].activity_id == activity.activity_id
    assert result.query_id
