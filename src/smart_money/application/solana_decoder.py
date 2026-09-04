from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload


@dataclass(frozen=True, slots=True)
class SolanaTransactionEnvelope:
    signature: str
    slot: int
    block_time: int | None
    message: Mapping[str, Any]
    envelope_id: str
    schema_version: str = "solana_transaction_envelope.v1"

    def __post_init__(self) -> None:
        if not self.signature.strip() or self.slot < 0:
            raise ValueError("invalid transaction envelope")
        if not isinstance(self.message, Mapping) or not self.message:
            raise ValueError("message must be non-empty mapping")
        identity = {"block_time": self.block_time, "message": dict(self.message),
                    "schema_version": self.schema_version, "signature": self.signature.strip(), "slot": self.slot}
        if self.envelope_id != deterministic_id("solana_transaction_envelope", identity):
            raise ValueError("envelope_id mismatch")


def build_transaction_envelope(signature: str, slot: int, message: Mapping[str, Any], block_time: int | None = None) -> SolanaTransactionEnvelope:
    identity = {"block_time": block_time, "message": dict(message), "schema_version": "solana_transaction_envelope.v1",
                "signature": signature.strip(), "slot": slot}
    return SolanaTransactionEnvelope(signature, slot, block_time, message,
                                     deterministic_id("solana_transaction_envelope", identity))


def parse_message_instructions(envelope: SolanaTransactionEnvelope) -> tuple[Mapping[str, Any], ...]:
    instructions = envelope.message.get("instructions")
    if not isinstance(instructions, (list, tuple)) or not all(isinstance(item, Mapping) for item in instructions):
        raise ValueError("instructions must be a sequence of mappings")
    return tuple(dict(item) for item in instructions)


def normalize_account_keys(keys: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if not isinstance(keys, (tuple, list)) or not all(isinstance(key, str) and key.strip() for key in keys):
        raise ValueError("account keys must be non-empty text")
    return tuple(dict.fromkeys(key.strip() for key in keys))


@dataclass(frozen=True, slots=True)
class TokenBalanceDelta:
    owner: str
    mint: str
    delta: int
    delta_id: str
    schema_version: str = "solana_token_balance_delta.v1"

    def __post_init__(self) -> None:
        if not self.owner.strip() or not self.mint.strip():
            raise ValueError("owner and mint are required")
        identity = {"delta": self.delta, "mint": self.mint.strip(), "owner": self.owner.strip(),
                    "schema_version": self.schema_version}
        if self.delta_id != deterministic_id("solana_token_balance_delta", identity):
            raise ValueError("delta_id mismatch")


class InstructionKind(str, Enum):
    TRANSFER = "TRANSFER"
    SWAP = "SWAP"
    LIQUIDITY = "LIQUIDITY"
    UNKNOWN = "UNKNOWN"


def classify_instruction(instruction: Mapping[str, Any]) -> InstructionKind:
    value = str(instruction.get("type", "")).upper()
    return InstructionKind(value) if value in InstructionKind._value2member_map_ else InstructionKind.UNKNOWN


@dataclass(frozen=True, slots=True)
class SwapInstruction:
    program: str
    wallet: str
    token_in: str
    token_out: str
    amount_in: int
    amount_out: int
    swap_id: str


def decode_swap_instruction(instruction: Mapping[str, Any]) -> SwapInstruction:
    if classify_instruction(instruction) is not InstructionKind.SWAP:
        raise ValueError("instruction is not a swap")
    identity = {"amount_in": instruction["amount_in"], "amount_out": instruction["amount_out"],
                "program": instruction["program"], "token_in": instruction["token_in"],
                "token_out": instruction["token_out"], "wallet": instruction["wallet"]}
    return SwapInstruction(instruction["program"], instruction["wallet"], instruction["token_in"],
                           instruction["token_out"], instruction["amount_in"], instruction["amount_out"],
                           deterministic_id("solana_swap_instruction", identity))


def decode_liquidity_event(instruction: Mapping[str, Any]) -> Mapping[str, Any]:
    if classify_instruction(instruction) is not InstructionKind.LIQUIDITY:
        raise ValueError("instruction is not liquidity")
    return dict(instruction)


def project_decoder_evidence(envelope: SolanaTransactionEnvelope) -> EvidencePayload:
    payload = {"envelope": {"envelope_id": envelope.envelope_id, "signature": envelope.signature,
                            "slot": envelope.slot, "message": dict(envelope.message)}}
    return EvidencePayload(source_id="solana-decoder", evidence_type="solana_decoder_evidence",
                           timestamp=envelope.slot, data=payload,
                           metadata={"authority": "EXTERNAL_NON_AUTHORITATIVE", "classification": "EVIDENCE",
                                     "verification_status": "UNKNOWN",
                                     "provenance": {"envelope_id": envelope.envelope_id}})


def verify_decoder_replay(envelope: SolanaTransactionEnvelope, payload: EvidencePayload) -> bool:
    return project_decoder_evidence(envelope).get_canonical_id() == payload.get_canonical_id()


def project_wallet_token_activity(envelope: SolanaTransactionEnvelope) -> EvidencePayload:
    return EvidencePayload(source_id="solana-decoder", evidence_type="solana_wallet_token_activity",
                           timestamp=envelope.slot,
                           data={"signature": envelope.signature, "slot": envelope.slot,
                                 "instructions": [dict(item) for item in parse_message_instructions(envelope)]},
                           metadata={"authority": "EXTERNAL_NON_AUTHORITATIVE", "classification": "EVIDENCE",
                                     "verification_status": "UNKNOWN",
                                     "provenance": {"envelope_id": envelope.envelope_id}})


__all__ = ["SolanaTransactionEnvelope", "build_transaction_envelope", "parse_message_instructions",
           "normalize_account_keys", "TokenBalanceDelta", "InstructionKind", "classify_instruction",
           "SwapInstruction", "decode_swap_instruction", "decode_liquidity_event",
           "project_decoder_evidence", "verify_decoder_replay", "project_wallet_token_activity"]
