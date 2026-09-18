from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class FirstLiquidityObservation:
    token_id: str
    pool_id: str
    liquidity_units: int
    observed_slot: int
    source_id: str
    observation_id: str
    schema_version: str = "first_liquidity_observation.v1"

    def __post_init__(self) -> None:
        for field in ("token_id", "pool_id", "source_id"):
            if not isinstance(getattr(self, field), str) or not getattr(self, field).strip():
                raise ValueError(f"{field} must be non-empty")
        for field in ("liquidity_units", "observed_slot"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field} must be non-negative integer")
        if self.liquidity_units == 0:
            raise ValueError("liquidity_units must be positive")
        if self.schema_version != "first_liquidity_observation.v1":
            raise ValueError("unsupported schema_version")
        if self.observation_id != deterministic_id("first_liquidity_observation", self._identity()):
            raise ValueError("observation_id does not match observation")

    def _identity(self) -> dict[str, Any]:
        return {"liquidity_units": self.liquidity_units, "observed_slot": self.observed_slot,
                "pool_id": self.pool_id.strip(), "schema_version": self.schema_version,
                "source_id": self.source_id.strip(), "token_id": self.token_id.strip()}

    def canonical_dict(self) -> dict[str, Any]:
        return {**self._identity(), "observation_id": self.observation_id}


def detect_first_liquidity(token_id: str, pool_id: str, liquidity_units: int,
                           observed_slot: int, source_id: str) -> FirstLiquidityObservation:
    identity = {"liquidity_units": liquidity_units, "observed_slot": observed_slot,
                "pool_id": pool_id.strip(), "schema_version": "first_liquidity_observation.v1",
                "source_id": source_id.strip(), "token_id": token_id.strip()}
    return FirstLiquidityObservation(token_id, pool_id, liquidity_units, observed_slot, source_id,
                                     deterministic_id("first_liquidity_observation", identity))


__all__ = ["FirstLiquidityObservation", "detect_first_liquidity"]
