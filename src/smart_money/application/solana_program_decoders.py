from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

PROGRAMS = {
    "raydium": "RAYDIUM",
    "jupiter": "JUPITER",
    "orca": "ORCA",
    "pumpfun": "PUMP_FUN",
}


def program_kind(program_id: str) -> str:
    try:
        return PROGRAMS[program_id.strip().lower()]
    except (AttributeError, KeyError) as exc:
        raise ValueError("unknown Solana program") from exc


@dataclass(frozen=True, slots=True)
class DecodedProgramEvent:
    program: str
    event_kind: str
    fields: Mapping[str, Any]
    event_id: str

    def __post_init__(self) -> None:
        if self.program not in PROGRAMS.values() or not self.event_kind.strip():
            raise ValueError("invalid program event")
        if self.event_id != deterministic_id("solana_program_event", self.identity_payload()):
            raise ValueError("event_id mismatch")

    def identity_payload(self) -> dict[str, Any]:
        return {"event_kind": self.event_kind, "fields": dict(self.fields),
                "program": self.program, "schema_version": "solana_program_event.v1"}


def decode_program_instruction(program_id: str, instruction: Mapping[str, Any]) -> DecodedProgramEvent:
    kind = program_kind(program_id)
    if not isinstance(instruction, Mapping) or not instruction:
        raise ValueError("instruction must be non-empty mapping")
    event_kind = {
        "RAYDIUM": "SWAP" if instruction.get("type") == "SWAP" else "LIQUIDITY",
        "JUPITER": "SWAP",
        "ORCA": "SWAP",
        "PUMP_FUN": "LAUNCH",
    }[kind]
    fields = dict(instruction)
    identity = {"event_kind": event_kind, "fields": fields,
                "program": kind, "schema_version": "solana_program_event.v1"}
    return DecodedProgramEvent(kind, event_kind, fields,
                               deterministic_id("solana_program_event", identity))


def project_token_balance_delta(owner: str, mint: str, delta: int, slot: int) -> EvidencePayload:
    if not owner.strip() or not mint.strip() or not isinstance(delta, int) or isinstance(delta, bool):
        raise ValueError("invalid balance delta")
    return EvidencePayload(
        source_id="solana-decoder", evidence_type="token_balance_delta",
        timestamp=slot, data={"owner": owner.strip(), "mint": mint.strip(), "delta": delta},
        metadata={"authority": "EXTERNAL_NON_AUTHORITATIVE", "classification": "EVIDENCE",
                  "verification_status": "UNKNOWN", "provenance": {"slot": str(slot)}},
    )


def project_swap_evidence(event: DecodedProgramEvent, slot: int) -> EvidencePayload:
    if event.event_kind != "SWAP":
        raise ValueError("event is not swap")
    return EvidencePayload(source_id="solana-decoder", evidence_type="real_swap_evidence",
                           timestamp=slot, data={"event": event.identity_payload()},
                           metadata={"authority": "EXTERNAL_NON_AUTHORITATIVE", "classification": "EVIDENCE",
                                     "verification_status": "UNKNOWN",
                                     "provenance": {"event_id": event.event_id}})


def project_liquidity_evidence(event: DecodedProgramEvent, slot: int) -> EvidencePayload:
    if event.event_kind not in {"LIQUIDITY", "LAUNCH"}:
        raise ValueError("event is not liquidity-related")
    return EvidencePayload(source_id="solana-decoder", evidence_type="liquidity_event_evidence",
                           timestamp=slot, data={"event": event.identity_payload()},
                           metadata={"authority": "EXTERNAL_NON_AUTHORITATIVE", "classification": "EVIDENCE",
                                     "verification_status": "UNKNOWN",
                                     "provenance": {"event_id": event.event_id}})


def ingest_wallet_token_activity(ledger: EvidenceLedger, payload: EvidencePayload) -> str:
    if not isinstance(ledger, EvidenceLedger) or not isinstance(payload, EvidencePayload):
        raise TypeError("invalid ledger or payload")
    canonical_id = payload.get_canonical_id()
    if ledger.append(payload) != canonical_id:
        raise ValueError("ledger identity mismatch")
    return canonical_id


def discover_smart_money_candidates(ledger: EvidenceLedger, *, min_swap_events: int = 1) -> tuple[dict[str, Any], ...]:
    if not isinstance(ledger, EvidenceLedger) or min_swap_events < 1:
        raise ValueError("invalid discovery inputs")
    grouped: dict[str, int] = {}
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "real_swap_evidence":
            continue
        event = payload.data.get("event", {})
        wallet = event.get("fields", {}).get("wallet")
        if isinstance(wallet, str) and wallet.strip():
            grouped[wallet.strip()] = grouped.get(wallet.strip(), 0) + 1
    return tuple({"wallet": wallet, "swap_count": count,
                  "candidate_id": deterministic_id("smart_money_candidate",
                                                    {"swap_count": count, "wallet": wallet})}
                 for wallet, count in sorted(grouped.items()) if count >= min_swap_events)


__all__ = [
    "PROGRAMS", "program_kind", "DecodedProgramEvent", "decode_program_instruction",
    "project_token_balance_delta", "project_swap_evidence", "project_liquidity_evidence",
    "ingest_wallet_token_activity", "discover_smart_money_candidates",
]
