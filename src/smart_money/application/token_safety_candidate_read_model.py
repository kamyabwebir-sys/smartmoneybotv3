from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.token_safety_candidate_binding import TokenSafetyCandidateBinding
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateReadRow:
    candidate: SolanaWalletTokenCandidate
    binding: TokenSafetyCandidateBinding
    binding_evidence_id: str
    replay_verified: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "binding": self.binding.canonical_dict(),
            "binding_evidence_id": self.binding_evidence_id,
            "candidate": self.candidate.canonical_dict(),
            "replay_verified": self.replay_verified,
        }


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateReadModel:
    rows: tuple[TokenSafetyCandidateReadRow, ...]
    model_id: str
    schema_version: str = "token_safety_candidate_read_model.v1"

    def __post_init__(self) -> None:
        if self.model_id != deterministic_id(
            "token_safety_candidate_read_model",
            {"rows": tuple(row.canonical_dict() for row in self.rows), "schema_version": self.schema_version},
        ):
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {"model_id": self.model_id, "rows": tuple(row.canonical_dict() for row in self.rows), "schema_version": self.schema_version}


def build_token_safety_candidate_read_model(
    ledger: EvidenceLedger,
) -> TokenSafetyCandidateReadModel:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    candidates: dict[str, SolanaWalletTokenCandidate] = {}
    bindings: list[tuple[TokenSafetyCandidateBinding, str]] = []
    for payload in ledger.iter_payloads():
        data = payload.data
        if payload.evidence_type == "solana_wallet_token_candidate":
            value = data.get("candidate")
            candidates[value["candidate_id"]] = SolanaWalletTokenCandidate(
                wallet=value["wallet"], mint=value["mint"], activity_count=value["activity_count"],
                buy_count=value["buy_count"], first_slot=value["first_slot"], last_slot=value["last_slot"],
                reasons=tuple(value["reasons"]), candidate_id=value["candidate_id"], schema_version=value["schema_version"],
            )
        elif payload.evidence_type == "token_safety_candidate_binding":
            value = data.get("binding")
            bindings.append((TokenSafetyCandidateBinding(
                candidate_id=value["candidate_id"], token_observation_id=value["token_observation_id"],
                wallet=value["wallet"], token=value["token"], liquidity_amount=value["liquidity_amount"],
                holder_concentration_bps=value["holder_concentration_bps"], mint_authority=value["mint_authority"],
                freeze_authority=value["freeze_authority"], update_authority=value["update_authority"],
                binding_id=value["binding_id"], schema_version=value["schema_version"],
            ), payload.get_canonical_id()))
    rows = []
    for binding, evidence_id in bindings:
        candidate = candidates.get(binding.candidate_id)
        if candidate is None:
            raise ValueError("binding candidate evidence is missing")
        if candidate.mint != binding.token or candidate.wallet != binding.wallet:
            raise ValueError("candidate and binding identity mismatch")
        rows.append(TokenSafetyCandidateReadRow(candidate, binding, evidence_id, True))
    rows.sort(key=lambda row: (row.candidate.first_slot, row.candidate.wallet, row.candidate.mint))
    identity = {"rows": tuple(row.canonical_dict() for row in rows), "schema_version": "token_safety_candidate_read_model.v1"}
    return TokenSafetyCandidateReadModel(tuple(rows), deterministic_id("token_safety_candidate_read_model", identity))


__all__ = ["TokenSafetyCandidateReadModel", "TokenSafetyCandidateReadRow", "build_token_safety_candidate_read_model"]
