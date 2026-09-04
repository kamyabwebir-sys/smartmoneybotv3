from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class TokenMetadataObservation:
    token_id: str
    name: str
    symbol: str
    decimals: int
    source_id: str
    observed_slot: int
    observation_id: str
    schema_version: str = "token_metadata_observation.v1"

    def __post_init__(self) -> None:
        for field in ("token_id", "name", "symbol", "source_id"):
            if not isinstance(getattr(self, field), str) or not getattr(self, field).strip():
                raise ValueError(f"{field} must be non-empty")
        if isinstance(self.decimals, bool) or not isinstance(self.decimals, int) or not 0 <= self.decimals <= 255:
            raise ValueError("decimals must be between 0 and 255")
        if isinstance(self.observed_slot, bool) or not isinstance(self.observed_slot, int) or self.observed_slot < 0:
            raise ValueError("observed_slot must be non-negative")
        if self.schema_version != "token_metadata_observation.v1":
            raise ValueError("unsupported schema_version")
        if self.observation_id != deterministic_id("token_metadata_observation", self._identity()):
            raise ValueError("observation_id does not match observation")

    def _identity(self) -> dict[str, Any]:
        return {k: v for k, v in {
            "decimals": self.decimals, "name": self.name.strip(), "observed_slot": self.observed_slot,
            "schema_version": self.schema_version, "source_id": self.source_id.strip(),
            "symbol": self.symbol.strip(), "token_id": self.token_id.strip(),
        }.items()}

    def canonical_dict(self) -> dict[str, Any]:
        return {**self._identity(), "observation_id": self.observation_id}


def build_token_metadata_observation(token_id: str, name: str, symbol: str, decimals: int,
                                     source_id: str, observed_slot: int) -> TokenMetadataObservation:
    identity = {"decimals": decimals, "name": name.strip(), "observed_slot": observed_slot,
                "schema_version": "token_metadata_observation.v1", "source_id": source_id.strip(),
                "symbol": symbol.strip(), "token_id": token_id.strip()}
    return TokenMetadataObservation(token_id, name, symbol, decimals, source_id, observed_slot,
                                    deterministic_id("token_metadata_observation", identity))


__all__ = ["TokenMetadataObservation", "build_token_metadata_observation"]
