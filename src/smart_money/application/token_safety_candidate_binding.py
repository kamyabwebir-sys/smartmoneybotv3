from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.core.ids import deterministic_id
from smart_money.domain.token_safety import TokenSafetyObservation


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateBinding:
    candidate_id: str
    token_observation_id: str
    wallet: str
    token: str
    liquidity_amount: int
    holder_concentration_bps: int
    mint_authority: str | None
    freeze_authority: str | None
    update_authority: str | None
    binding_id: str
    schema_version: str = "token_safety_candidate_binding.v1"

    def __post_init__(self) -> None:
        for name in ("candidate_id", "token_observation_id", "wallet", "token", "binding_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        for name in ("liquidity_amount", "holder_concentration_bps"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.holder_concentration_bps > 10000:
            raise ValueError("holder_concentration_bps must be <= 10000")
        for name in ("mint_authority", "freeze_authority", "update_authority"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be non-empty text or None")
        if self.schema_version != "token_safety_candidate_binding.v1":
            raise ValueError("unsupported binding schema_version")
        if self.binding_id != deterministic_id(
            "token_safety_candidate_binding", self.identity_payload()
        ):
            raise ValueError("binding_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "freeze_authority": self.freeze_authority,
            "holder_concentration_bps": self.holder_concentration_bps,
            "liquidity_amount": self.liquidity_amount,
            "mint_authority": self.mint_authority,
            "schema_version": self.schema_version,
            "token": self.token.strip(),
            "token_observation_id": self.token_observation_id,
            "update_authority": self.update_authority,
            "wallet": self.wallet.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"binding_id": self.binding_id, **self.identity_payload()}


def bind_token_safety_to_candidate(
    candidate: SolanaWalletTokenCandidate,
    observation: TokenSafetyObservation,
) -> TokenSafetyCandidateBinding:
    if not isinstance(candidate, SolanaWalletTokenCandidate):
        raise TypeError("candidate must be SolanaWalletTokenCandidate")
    if not isinstance(observation, TokenSafetyObservation):
        raise TypeError("observation must be TokenSafetyObservation")
    if candidate.mint != observation.token:
        raise ValueError("candidate mint and token observation mismatch")
    identity = {
        "candidate_id": candidate.candidate_id,
        "freeze_authority": observation.freeze_authority,
        "holder_concentration_bps": observation.holder_concentration_bps,
        "liquidity_amount": observation.liquidity_amount,
        "mint_authority": observation.mint_authority,
        "schema_version": "token_safety_candidate_binding.v1",
        "token": observation.token,
        "token_observation_id": observation.observation_id,
        "update_authority": observation.update_authority,
        "wallet": candidate.wallet,
    }
    return TokenSafetyCandidateBinding(
        candidate_id=candidate.candidate_id,
        token_observation_id=observation.observation_id,
        wallet=candidate.wallet,
        token=observation.token,
        liquidity_amount=observation.liquidity_amount,
        holder_concentration_bps=observation.holder_concentration_bps,
        mint_authority=observation.mint_authority,
        freeze_authority=observation.freeze_authority,
        update_authority=observation.update_authority,
        binding_id=deterministic_id("token_safety_candidate_binding", identity),
    )


__all__ = ["TokenSafetyCandidateBinding", "bind_token_safety_to_candidate"]
