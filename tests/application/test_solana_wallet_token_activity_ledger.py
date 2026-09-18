from smart_money.application.solana_swap_evidence import extract_solana_swap_evidence
from smart_money.application.solana_wallet_token_activity import build_solana_wallet_token_activity
from smart_money.application.solana_wallet_token_activity_ledger import ingest_solana_wallet_token_activity
from smart_money.domain.solana_observation import SolanaChainObservation
from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger


def test_activity_is_projected_idempotently(tmp_path):
    raw = {
        "slot": 7, "transaction": {"signatures": ["sig"], "message": {"accountKeys": [{"pubkey": "program"}]}},
        "meta": {"preBalances": [100], "postBalances": [90],
                 "preTokenBalances": [{"accountIndex": 1, "mint": "M", "owner": "W", "uiTokenAmount": {"amount": "0", "decimals": 0}}],
                 "postTokenBalances": [{"accountIndex": 1, "mint": "M", "owner": "W", "uiTokenAmount": {"amount": "2", "decimals": 0}}]},
    }
    observation = SolanaChainObservation(slot=7, observed_at=1, transaction_signature="sig", program_id="program", subject="program")
    activity = build_solana_wallet_token_activity(observation, extract_solana_swap_evidence(raw, owner="W", mint="M"))
    ledger = EvidenceGroundingLedger()
    first = ingest_solana_wallet_token_activity(activity, ledger)
    second = ingest_solana_wallet_token_activity(activity, ledger)
    assert first.evidence_id == second.evidence_id
    assert second.already_present is True
