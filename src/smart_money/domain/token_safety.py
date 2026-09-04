from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class TokenSafetyObservation:
    token: str
    observed_at: int
    mint_authority: str | None
    freeze_authority: str | None
    update_authority: str | None
    liquidity_amount: int
    holder_concentration_bps: int
    deployer: str
    observation_id: str
    schema_version: str = "token_safety_observation.v1"

    def __post_init__(self) -> None:
        for name in ("token", "deployer", "observation_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if isinstance(self.observed_at, bool) or not isinstance(self.observed_at, int) or self.observed_at < 0:
            raise ValueError("observed_at must be non-negative")
        for name in ("mint_authority", "freeze_authority", "update_authority"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be non-empty text or None")
        for name in ("liquidity_amount", "holder_concentration_bps"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.holder_concentration_bps > 10000:
            raise ValueError("holder_concentration_bps must be <= 10000")
        if self.schema_version != "token_safety_observation.v1":
            raise ValueError("unsupported token safety schema_version")
        if self.observation_id != deterministic_id(
            "token_safety_observation", self.identity_payload()
        ):
            raise ValueError("observation_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "deployer": self.deployer.strip(),
            "freeze_authority": self.freeze_authority,
            "holder_concentration_bps": self.holder_concentration_bps,
            "liquidity_amount": self.liquidity_amount,
            "mint": self.mint_authority,
            "observed_at": self.observed_at,
            "schema_version": self.schema_version,
            "token": self.token.strip(),
            "update_authority": self.update_authority,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"observation_id": self.observation_id, **self.identity_payload()}


__all__ = ["TokenSafetyObservation"]
