"""Deterministic signer, account-key and token-owner resolution for RPC results."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaAccountResolution:
    fee_payer: str
    signers: tuple[str, ...]
    account_keys: tuple[str, ...]
    token_account_owners: tuple[tuple[int, str, str], ...]
    resolution_id: str
    schema_version: str = "solana_account_resolution.v1"

    def canonical_dict(self) -> dict[str, object]:
        return {
            "account_keys": self.account_keys,
            "fee_payer": self.fee_payer,
            "resolution_id": self.resolution_id,
            "schema_version": self.schema_version,
            "signers": self.signers,
            "token_account_owners": self.token_account_owners,
        }


def _key(value: object) -> str:
    candidate = value.get("pubkey") if isinstance(value, Mapping) else value
    if not isinstance(candidate, str) or not candidate.strip():
        raise ValueError("account key must be non-empty text")
    return candidate.strip()


def _rows(value: object, name: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence")
    return value


def resolve_solana_accounts(raw: Mapping[str, Any]) -> SolanaAccountResolution:
    if not isinstance(raw, Mapping):
        raise TypeError("raw transaction must be a mapping")
    transaction = raw.get("transaction")
    meta = raw.get("meta")
    if not isinstance(transaction, Mapping) or not isinstance(meta, Mapping):
        raise TypeError("transaction and meta must be mappings")
    message = transaction.get("message")
    if not isinstance(message, Mapping):
        raise TypeError("transaction message must be a mapping")
    raw_keys = _rows(message.get("accountKeys"), "accountKeys")
    if not raw_keys:
        raise ValueError("accountKeys must be non-empty")
    keys = [_key(value) for value in raw_keys]
    loaded = meta.get("loadedAddresses")
    if isinstance(loaded, Mapping):
        for group in ("writable", "readonly"):
            for value in _rows(loaded.get(group, ()), f"loadedAddresses.{group}"):
                address = _key(value)
                if address not in keys:
                    keys.append(address)
    if len(set(keys)) != len(keys):
        raise ValueError("resolved account keys must be unique")

    explicit = tuple(
        _key(value)
        for value in raw_keys
        if isinstance(value, Mapping) and value.get("signer") is True
    )
    header = message.get("header")
    if explicit:
        signers = explicit
    elif isinstance(header, Mapping):
        required = header.get("numRequiredSignatures")
        if isinstance(required, bool) or not isinstance(required, int) or not 1 <= required <= len(raw_keys):
            raise ValueError("numRequiredSignatures is invalid")
        signers = tuple(keys[:required])
    else:
        signers = (keys[0],)

    owners: dict[int, tuple[str, str]] = {}
    for side in ("preTokenBalances", "postTokenBalances"):
        for row in _rows(meta.get(side, ()), side):
            if not isinstance(row, Mapping):
                raise TypeError("token balance row must be a mapping")
            index, owner, mint = row.get("accountIndex"), row.get("owner"), row.get("mint")
            if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(keys):
                raise ValueError("token account index is invalid")
            if not isinstance(owner, str) or not owner.strip() or not isinstance(mint, str) or not mint.strip():
                raise ValueError("token owner and mint are required")
            identity = (owner.strip(), mint.strip())
            if index in owners and owners[index] != identity:
                raise ValueError("token account ownership changed")
            owners[index] = identity
    owner_rows = tuple((index, owner, mint) for index, (owner, mint) in sorted(owners.items()))
    identity = {
        "account_keys": tuple(keys),
        "fee_payer": keys[0],
        "schema_version": "solana_account_resolution.v1",
        "signers": signers,
        "token_account_owners": owner_rows,
    }
    return SolanaAccountResolution(
        fee_payer=keys[0],
        signers=signers,
        account_keys=tuple(keys),
        token_account_owners=owner_rows,
        resolution_id=deterministic_id("solana-account-resolution", identity),
    )


__all__ = ["SolanaAccountResolution", "resolve_solana_accounts"]
