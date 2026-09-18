from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.token_safety_candidate_binding import TokenSafetyCandidateBinding
from smart_money.application.token_safety_candidate_summary_binding import (
    TokenSafetyCandidateSummaryBinding,
)
from smart_money.application.token_safety_candidate_summary_replay import (
    replay_verify_token_safety_candidate_summary_binding,
)
from smart_money.application.token_safety_evidence_summary import TokenSafetyEvidenceSummary
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "token_safety_candidate_summary_read_model.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateSummaryReadRow:
    binding: TokenSafetyCandidateSummaryBinding
    evidence_id: str
    replay_verified: bool

    def __post_init__(self) -> None:
        if not isinstance(self.binding, TokenSafetyCandidateSummaryBinding):
            raise TypeError("binding must be TokenSafetyCandidateSummaryBinding")
        if not isinstance(self.evidence_id, str) or not self.evidence_id.strip():
            raise ValueError("evidence_id must be non-empty")
        if not isinstance(self.replay_verified, bool):
            raise TypeError("replay_verified must be boolean")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "binding": self.binding.canonical_dict(),
            "evidence_id": self.evidence_id,
            "replay_verified": self.replay_verified,
        }


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateSummaryReadModel:
    rows: tuple[TokenSafetyCandidateSummaryReadRow, ...]
    model_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported read model schema_version")
        expected = deterministic_id(
            "token_safety_candidate_summary_read_model",
            {
                "rows": tuple(row.canonical_dict() for row in self.rows),
                "schema_version": self.schema_version,
            },
        )
        if self.model_id != expected:
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "rows": tuple(row.canonical_dict() for row in self.rows),
            "schema_version": self.schema_version,
        }


def build_token_safety_candidate_summary_read_model(
    ledger: EvidenceLedger, *, verify_replay: bool = True
) -> TokenSafetyCandidateSummaryReadModel:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if not isinstance(verify_replay, bool):
        raise TypeError("verify_replay must be boolean")
    rows: list[TokenSafetyCandidateSummaryReadRow] = []
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "token_safety_candidate_summary_binding":
            continue
        data = payload.data.get("binding")
        if not hasattr(data, "get"):
            raise ValueError("invalid candidate safety summary payload in Ledger")
        candidate_data = data["candidate"]
        safety_data = data["safety_binding"]
        summary_data = data["summary"]
        candidate = SolanaWalletTokenCandidate(
            wallet=candidate_data["wallet"],
            mint=candidate_data["mint"],
            activity_count=candidate_data["activity_count"],
            buy_count=candidate_data["buy_count"],
            first_slot=candidate_data["first_slot"],
            last_slot=candidate_data["last_slot"],
            reasons=tuple(candidate_data["reasons"]),
            candidate_id=candidate_data["candidate_id"],
            schema_version=candidate_data["schema_version"],
        )
        safety_binding = TokenSafetyCandidateBinding(
            candidate_id=safety_data["candidate_id"],
            token_observation_id=safety_data["token_observation_id"],
            wallet=safety_data["wallet"],
            token=safety_data["token"],
            liquidity_amount=safety_data["liquidity_amount"],
            holder_concentration_bps=safety_data["holder_concentration_bps"],
            mint_authority=safety_data["mint_authority"],
            freeze_authority=safety_data["freeze_authority"],
            update_authority=safety_data["update_authority"],
            binding_id=safety_data["binding_id"],
            schema_version=safety_data["schema_version"],
        )
        summary = TokenSafetyEvidenceSummary(
            observation_id=summary_data["observation_id"],
            total_rules=summary_data["total_rules"],
            triggered_rules=summary_data["triggered_rules"],
            triggered_rule_ids=tuple(summary_data["triggered_rule_ids"]),
            triggered_reasons=tuple(summary_data["triggered_reasons"]),
            summary_id=summary_data["summary_id"],
            schema_version=summary_data["schema_version"],
        )
        binding = TokenSafetyCandidateSummaryBinding(
            candidate=candidate,
            binding=safety_binding,
            summary=summary,
            binding_id=data["binding_id"],
            schema_version=data["schema_version"],
        )
        replay_verified = (
            replay_verify_token_safety_candidate_summary_binding(binding, ledger).matches
            if verify_replay
            else False
        )
        rows.append(
            TokenSafetyCandidateSummaryReadRow(
                binding=binding,
                evidence_id=payload.get_canonical_id(),
                replay_verified=replay_verified,
            )
        )
    rows.sort(
        key=lambda row: (
            row.binding.candidate.first_slot,
            row.binding.candidate.wallet,
            row.binding.candidate.mint,
            row.binding.binding_id,
        )
    )
    identity = {
        "rows": tuple(row.canonical_dict() for row in rows),
        "schema_version": _SCHEMA_VERSION,
    }
    return TokenSafetyCandidateSummaryReadModel(
        rows=tuple(rows),
        model_id=deterministic_id(
            "token_safety_candidate_summary_read_model", identity
        ),
    )


__all__ = [
    "TokenSafetyCandidateSummaryReadModel",
    "TokenSafetyCandidateSummaryReadRow",
    "build_token_safety_candidate_summary_read_model",
]
