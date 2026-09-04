from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.token_safety_candidate_binding import TokenSafetyCandidateBinding
from smart_money.application.token_safety_evidence_summary import TokenSafetyEvidenceSummary
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "token_safety_candidate_summary_binding.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateSummaryBinding:
    candidate: SolanaWalletTokenCandidate
    binding: TokenSafetyCandidateBinding
    summary: TokenSafetyEvidenceSummary
    binding_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.candidate, SolanaWalletTokenCandidate):
            raise TypeError("candidate must be SolanaWalletTokenCandidate")
        if not isinstance(self.binding, TokenSafetyCandidateBinding):
            raise TypeError("binding must be TokenSafetyCandidateBinding")
        if not isinstance(self.summary, TokenSafetyEvidenceSummary):
            raise TypeError("summary must be TokenSafetyEvidenceSummary")
        if not isinstance(self.binding_id, str) or not self.binding_id.strip():
            raise ValueError("binding_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported candidate summary binding schema_version")
        if self.candidate.candidate_id != self.binding.candidate_id:
            raise ValueError("candidate and safety binding identity mismatch")
        if self.candidate.mint != self.binding.token:
            raise ValueError("candidate and safety token mismatch")
        if self.summary.observation_id != self.binding.token_observation_id:
            raise ValueError("summary and safety observation mismatch")
        if self.binding_id != deterministic_id(
            "token_safety_candidate_summary_binding", self.identity_payload()
        ):
            raise ValueError("binding_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate.candidate_id,
            "schema_version": self.schema_version,
            "summary_id": self.summary.summary_id,
            "token_observation_id": self.binding.token_observation_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "candidate": self.candidate.canonical_dict(),
            "safety_binding": self.binding.canonical_dict(),
            "schema_version": self.schema_version,
            "summary": self.summary.canonical_dict(),
        }


def bind_candidate_safety_summary(
    candidate: SolanaWalletTokenCandidate,
    binding: TokenSafetyCandidateBinding,
    summary: TokenSafetyEvidenceSummary,
) -> TokenSafetyCandidateSummaryBinding:
    identity = {
        "candidate_id": candidate.candidate_id,
        "schema_version": _SCHEMA_VERSION,
        "summary_id": summary.summary_id,
        "token_observation_id": binding.token_observation_id,
    }
    return TokenSafetyCandidateSummaryBinding(
        candidate=candidate,
        binding=binding,
        summary=summary,
        binding_id=deterministic_id("token_safety_candidate_summary_binding", identity),
    )


__all__ = [
    "TokenSafetyCandidateSummaryBinding",
    "bind_candidate_safety_summary",
]
