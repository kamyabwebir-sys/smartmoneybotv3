from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_program_decoders import (
    decode_program_instruction, discover_smart_money_candidates, ingest_wallet_token_activity,
    program_kind, project_liquidity_evidence, project_swap_evidence,
    project_token_balance_delta,
)


def test_program_decoders_projection_and_candidate_discovery() -> None:
    assert program_kind("raydium") == "RAYDIUM"
    event = decode_program_instruction(
        "raydium", {"type": "SWAP", "wallet": "wallet-a", "token_in": "a", "token_out": "b"}
    )
    ledger = EvidenceGroundingLedger()
    ingest_wallet_token_activity(ledger, project_swap_evidence(event, 10))
    ingest_wallet_token_activity(ledger, project_token_balance_delta("wallet-a", "b", 5, 10))
    liquidity = decode_program_instruction("pumpfun", {"type": "LAUNCH", "token": "b"})
    ingest_wallet_token_activity(ledger, project_liquidity_evidence(liquidity, 11))
    assert discover_smart_money_candidates(ledger)[0]["wallet"] == "wallet-a"
