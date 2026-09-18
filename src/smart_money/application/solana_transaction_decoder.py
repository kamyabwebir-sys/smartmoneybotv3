from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from smart_money.domain.solana_observation import SolanaChainObservation


def decode_solana_transaction(
    raw: Mapping[str, Any], *, observed_at: int
) -> SolanaChainObservation:
    """Decode a JSON-RPC transaction result into a canonical observation.

    This deliberately extracts only stable identity and raw meta facts; protocol-
    specific swap interpretation belongs to a later slice.
    """
    if not isinstance(raw, Mapping):
        raise TypeError("raw transaction must be a mapping")
    if isinstance(observed_at, bool) or not isinstance(observed_at, int) or observed_at < 0:
        raise ValueError("observed_at must be a non-negative integer")
    required = {"slot", "transaction", "meta"}
    if not required.issubset(raw):
        raise ValueError("raw transaction is missing required keys")
    slot = raw["slot"]
    if isinstance(slot, bool) or not isinstance(slot, int) or slot < 0:
        raise ValueError("slot must be a non-negative integer")
    transaction = raw["transaction"]
    if not isinstance(transaction, Mapping):
        raise TypeError("transaction must be a mapping")
    message = transaction.get("message")
    if not isinstance(message, Mapping):
        raise ValueError("transaction.message must be a mapping")
    account_keys = message.get("accountKeys")
    if not isinstance(account_keys, list) or not account_keys:
        raise ValueError("transaction.message.accountKeys must be non-empty")
    signatures = transaction.get("signatures")
    signature = signatures[0] if isinstance(signatures, list) and signatures else None
    if not isinstance(signature, str) or not signature.strip():
        raise ValueError("transaction signature is missing")
    first_account = account_keys[0]
    if isinstance(first_account, Mapping):
        program_id = first_account.get("pubkey")
    else:
        program_id = first_account
    if not isinstance(program_id, str) or not program_id.strip():
        raise ValueError("program identity is missing")
    meta = raw["meta"]
    if not isinstance(meta, Mapping):
        raise TypeError("transaction meta must be a mapping")
    facts = {
        "err": meta.get("err"),
        "fee": meta.get("fee"),
        "pre_balances": meta.get("preBalances", []),
        "post_balances": meta.get("postBalances", []),
        "log_messages": meta.get("logMessages", []),
    }
    return SolanaChainObservation(
        slot=slot,
        observed_at=observed_at,
        transaction_signature=signature,
        program_id=program_id,
        subject=program_id,
        facts=facts,
        commitment="finalized",
    )


__all__ = ["decode_solana_transaction"]
