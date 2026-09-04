from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_swap_evidence import extract_solana_swap_evidence
from smart_money.application.solana_token_activity_aggregation import aggregate_solana_token_activity
from smart_money.application.solana_wallet_token_activity import build_solana_wallet_token_activity
from smart_money.application.solana_wallet_token_activity_ledger import ingest_solana_wallet_token_activity
from smart_money.domain.solana_observation import SolanaChainObservation


def test_token_activity_aggregation_counts_wallets_and_directions():
    raw = {
        "transaction": {"signatures": ["sig-token"]},
        "meta": {
            "preBalances": [100], "postBalances": [90],
            "preTokenBalances": [{"accountIndex": 1, "mint": "MINT", "owner": "WALLET",
                                  "uiTokenAmount": {"amount": "0", "decimals": 0}}],
            "postTokenBalances": [{"accountIndex": 1, "mint": "MINT", "owner": "WALLET",
                                   "uiTokenAmount": {"amount": "3", "decimals": 0}}],
        },
    }
    observation = SolanaChainObservation(
        slot=12, observed_at=1, transaction_signature="sig-token",
        program_id="program", subject="program"
    )
    activity = build_solana_wallet_token_activity(
        observation, extract_solana_swap_evidence(raw, owner="WALLET", mint="MINT")
    )
    ledger = EvidenceGroundingLedger()
    ingest_solana_wallet_token_activity(activity, ledger)
    aggregate = aggregate_solana_token_activity(ledger, mint="MINT")
    assert aggregate.activity_count == 1
    assert aggregate.wallet_count == 1
    assert aggregate.buy_count == 1
    assert aggregate.first_slot == aggregate.last_slot == 12
