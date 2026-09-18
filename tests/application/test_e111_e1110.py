from smart_money.application.solana_decoder import (
    InstructionKind, build_transaction_envelope, classify_instruction,
    decode_liquidity_event, decode_swap_instruction, normalize_account_keys,
    parse_message_instructions, project_decoder_evidence,
    project_wallet_token_activity, verify_decoder_replay,
)


def test_solana_decoder_pipeline() -> None:
    instruction = {"type": "SWAP", "program": "raydium", "wallet": "w",
                   "token_in": "a", "token_out": "b", "amount_in": 10, "amount_out": 9}
    envelope = build_transaction_envelope("sig", 10, {"instructions": [instruction]})
    assert parse_message_instructions(envelope)
    assert normalize_account_keys([" a ", "a", "b"]) == ("a", "b")
    assert classify_instruction(instruction) is InstructionKind.SWAP
    assert decode_swap_instruction(instruction).swap_id
    liquidity = {"type": "LIQUIDITY", "pool": "p", "amount": 100}
    assert decode_liquidity_event(liquidity)["pool"] == "p"
    evidence = project_decoder_evidence(envelope)
    assert verify_decoder_replay(envelope, evidence)
    assert project_wallet_token_activity(envelope).evidence_type == "solana_wallet_token_activity"
