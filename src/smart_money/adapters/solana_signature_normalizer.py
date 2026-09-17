from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from smart_money.domain.solana_observation import SolanaChainObservation

WRAPPED_SOL_MINT = "So11111111111111111111111111111111111111112"
QUOTE_MINTS = frozenset(
    {
        WRAPPED_SOL_MINT,
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    }
)

DEX_PROGRAMS = {
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9dQ5f1i8": "RAYDIUM",
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": "RAYDIUM_CLMM",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZ4vW3j6h5": "JUPITER",
    "whirLbMiicVdio4qvUfM5KAg6CtXGBH8r95GmZJDsL": "ORCA_WHIRLPOOL",
}


class TradeDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class RawTokenBalance:
    account_index: int
    mint: str
    owner: str
    raw_amount: int
    decimals: int

    def __post_init__(self) -> None:
        if self.account_index < 0 or self.raw_amount < 0 or self.decimals < 0:
            raise ValueError("token balance numeric values must be non-negative")
        if not self.mint.strip():
            raise ValueError("token balance mint must be non-empty")


@dataclass(frozen=True, slots=True)
class RawSolanaSignature:
    slot: int
    block_time: int | None
    signature: str
    signer: str
    fee: int
    native_pre_balance: int
    native_post_balance: int
    pre_token_balances: tuple[RawTokenBalance, ...]
    post_token_balances: tuple[RawTokenBalance, ...]
    program_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.slot < 0 or self.fee < 0:
            raise ValueError("slot and fee must be non-negative")
        if self.block_time is not None and self.block_time < 0:
            raise ValueError("block_time must be non-negative")
        if not self.signature.strip() or not self.signer.strip():
            raise ValueError("signature and signer must be non-empty")


@dataclass(frozen=True, slots=True)
class TokenBalanceDelta:
    account_index: int
    mint: str
    owner: str
    pre_amount: int
    post_amount: int
    delta: int
    decimals: int

    def canonical_dict(self) -> dict[str, object]:
        return {
            "account_index": self.account_index,
            "decimals": self.decimals,
            "delta": self.delta,
            "mint": self.mint,
            "owner": self.owner,
            "post_amount": self.post_amount,
            "pre_amount": self.pre_amount,
        }


@dataclass(frozen=True, slots=True)
class TradeClassification:
    direction: TradeDirection
    input_mints: tuple[str, ...]
    output_mints: tuple[str, ...]
    reason: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "direction": self.direction.value,
            "input_mints": self.input_mints,
            "output_mints": self.output_mints,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class NormalizedSolanaSignature:
    raw: RawSolanaSignature
    token_deltas: tuple[TokenBalanceDelta, ...]
    classification: TradeClassification
    observation: SolanaChainObservation

    def candidate_activity(self) -> dict[str, object]:
        return {
            "direction": self.classification.direction.value,
            "signature": self.raw.signature,
            "slot": self.raw.slot,
            "wallet": self.raw.signer,
        }


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    return value


def _sequence(value: object, name: str) -> Sequence[Any]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence")
    return value


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _integer(value: object, name: str, *, default: int | None = None) -> int:
    if value is None and default is not None:
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value


def _account_key(value: object) -> str:
    if isinstance(value, Mapping):
        return _text(value.get("pubkey"), "account key pubkey")
    return _text(value, "account key")


def _parse_token_balances(value: object) -> tuple[RawTokenBalance, ...]:
    rows: list[RawTokenBalance] = []
    for entry in _sequence(value, "token balances"):
        item = _mapping(entry, "token balance")
        amount = _mapping(item.get("uiTokenAmount"), "uiTokenAmount")
        raw_amount = amount.get("amount", "0")
        if not isinstance(raw_amount, str) or not raw_amount.isdigit():
            raise ValueError("token raw amount must be an unsigned integer string")
        owner = item.get("owner", "")
        if owner is None:
            owner = ""
        if not isinstance(owner, str):
            raise TypeError("token owner must be text")
        rows.append(
            RawTokenBalance(
                account_index=_integer(item.get("accountIndex"), "accountIndex"),
                mint=_text(item.get("mint"), "mint"),
                owner=owner.strip(),
                raw_amount=int(raw_amount),
                decimals=_integer(amount.get("decimals"), "decimals", default=0),
            )
        )
    return tuple(sorted(rows, key=lambda row: (row.account_index, row.mint, row.owner)))


def _program_ids(message: Mapping[str, Any], meta: Mapping[str, Any]) -> tuple[str, ...]:
    groups: list[object] = [message.get("instructions", ())]
    for group in meta.get("innerInstructions", ()) or ():
        if isinstance(group, Mapping):
            groups.append(group.get("instructions", ()))
    values: set[str] = set()
    for group in groups:
        for instruction in group or ():
            if not isinstance(instruction, Mapping):
                continue
            program_id = instruction.get("programId")
            if isinstance(program_id, str) and program_id.strip():
                values.add(program_id.strip())
    return tuple(sorted(values))


class SolanaSignatureNormalizer:
    """Normalize one JSON-RPC getTransaction result without network or disk I/O."""

    @classmethod
    def parse_raw(cls, payload: Mapping[str, Any]) -> RawSolanaSignature:
        if not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping")
        result_value = payload.get("result") if "result" in payload else payload
        result = _mapping(result_value, "transaction result")
        transaction = _mapping(result.get("transaction"), "transaction")
        message = _mapping(transaction.get("message"), "transaction.message")
        meta = _mapping(result.get("meta"), "meta")
        account_keys = _sequence(message.get("accountKeys"), "accountKeys")
        if not account_keys:
            raise ValueError("accountKeys must be non-empty")
        signer = _account_key(account_keys[0])
        for key in account_keys:
            if isinstance(key, Mapping) and key.get("signer") is True:
                signer = _account_key(key)
                break
        signatures = _sequence(transaction.get("signatures"), "signatures")
        if not signatures:
            raise ValueError("transaction signature is missing")
        pre_balances = _sequence(meta.get("preBalances"), "preBalances")
        post_balances = _sequence(meta.get("postBalances"), "postBalances")
        if not pre_balances or len(pre_balances) != len(post_balances):
            raise ValueError("native balance vectors must be non-empty and aligned")
        return RawSolanaSignature(
            slot=_integer(result.get("slot"), "slot"),
            block_time=(
                None
                if result.get("blockTime") is None
                else _integer(result.get("blockTime"), "blockTime")
            ),
            signature=_text(signatures[0], "signature"),
            signer=signer,
            fee=_integer(meta.get("fee"), "fee", default=0),
            native_pre_balance=_integer(pre_balances[0], "preBalances[0]"),
            native_post_balance=_integer(post_balances[0], "postBalances[0]"),
            pre_token_balances=_parse_token_balances(meta.get("preTokenBalances", ())),
            post_token_balances=_parse_token_balances(meta.get("postTokenBalances", ())),
            program_ids=_program_ids(message, meta),
        )

    @staticmethod
    def extract_token_balance_deltas(
        raw: RawSolanaSignature,
    ) -> tuple[TokenBalanceDelta, ...]:
        before = {row.account_index: row for row in raw.pre_token_balances}
        after = {row.account_index: row for row in raw.post_token_balances}
        deltas: list[TokenBalanceDelta] = []
        for index in sorted(set(before) | set(after)):
            pre = before.get(index)
            post = after.get(index)
            reference = post or pre
            assert reference is not None
            if (
                pre is not None
                and post is not None
                and (pre.mint != post.mint or pre.decimals != post.decimals)
            ):
                raise ValueError("token balance identity changed at one account index")
            owner = (post.owner if post and post.owner else pre.owner if pre else "")
            pre_amount = pre.raw_amount if pre else 0
            post_amount = post.raw_amount if post else 0
            delta = post_amount - pre_amount
            if delta:
                deltas.append(
                    TokenBalanceDelta(
                        account_index=index,
                        mint=reference.mint,
                        owner=owner,
                        pre_amount=pre_amount,
                        post_amount=post_amount,
                        delta=delta,
                        decimals=reference.decimals,
                    )
                )
        return tuple(deltas)

    @staticmethod
    def classify_trade(
        raw: RawSolanaSignature,
        deltas: tuple[TokenBalanceDelta, ...],
    ) -> TradeClassification:
        owned = tuple(row for row in deltas if row.owner == raw.signer)
        inflows = tuple(sorted({row.mint for row in owned if row.delta > 0}))
        outflows = tuple(sorted({row.mint for row in owned if row.delta < 0}))
        native_delta = raw.native_post_balance - raw.native_pre_balance
        quote_in = any(mint in QUOTE_MINTS for mint in inflows) or native_delta > raw.fee
        quote_out = any(mint in QUOTE_MINTS for mint in outflows) or native_delta < -raw.fee
        asset_in = any(mint not in QUOTE_MINTS for mint in inflows)
        asset_out = any(mint not in QUOTE_MINTS for mint in outflows)
        if quote_out and asset_in:
            direction, reason = TradeDirection.BUY, "quote_out_asset_in"
        elif asset_out and quote_in:
            direction, reason = TradeDirection.SELL, "asset_out_quote_in"
        else:
            direction, reason = TradeDirection.UNKNOWN, "insufficient_directional_evidence"
        return TradeClassification(direction, outflows, inflows, reason)

    @classmethod
    def normalize(
        cls,
        payload: Mapping[str, Any],
        *,
        observed_at: int | None = None,
        commitment: str = "finalized",
    ) -> NormalizedSolanaSignature:
        raw = cls.parse_raw(payload)
        timestamp = raw.block_time if observed_at is None else observed_at
        if timestamp is None:
            raise ValueError("observed_at is required when blockTime is absent")
        if isinstance(timestamp, bool) or not isinstance(timestamp, int) or timestamp < 0:
            raise ValueError("observed_at must be a non-negative integer")
        deltas = cls.extract_token_balance_deltas(raw)
        classification = cls.classify_trade(raw, deltas)
        dex_programs = tuple(
            program_id for program_id in raw.program_ids if program_id in DEX_PROGRAMS
        )
        program_id = dex_programs[0] if dex_programs else (
            raw.program_ids[0] if raw.program_ids else "unknown"
        )
        observation = SolanaChainObservation(
            slot=raw.slot,
            observed_at=timestamp,
            transaction_signature=raw.signature,
            program_id=program_id,
            subject=raw.signer,
            commitment=commitment,
            facts={
                "block_time": raw.block_time,
                "classification": classification.canonical_dict(),
                "dex_venues": tuple(
                    sorted({DEX_PROGRAMS[item] for item in dex_programs})
                ),
                "fee": raw.fee,
                "native_balance_delta": raw.native_post_balance
                - raw.native_pre_balance,
                "program_ids": raw.program_ids,
                "token_balance_deltas": tuple(
                    item.canonical_dict() for item in deltas
                ),
            },
        )
        return NormalizedSolanaSignature(raw, deltas, classification, observation)


__all__ = [
    "DEX_PROGRAMS",
    "NormalizedSolanaSignature",
    "RawSolanaSignature",
    "RawTokenBalance",
    "SolanaSignatureNormalizer",
    "TokenBalanceDelta",
    "TradeClassification",
    "TradeDirection",
]
