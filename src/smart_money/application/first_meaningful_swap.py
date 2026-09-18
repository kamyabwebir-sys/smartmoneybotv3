from __future__ import annotations

from dataclasses import dataclass
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class FirstMeaningfulSwapObservation:
    token_id: str
    wallet_id: str
    amount_units: int
    observed_slot: int
    source_id: str
    observation_id: str
    schema_version: str = "first_meaningful_swap_observation.v1"

    def __post_init__(self) -> None:
        for field in ("token_id", "wallet_id", "source_id"):
            if not isinstance(getattr(self, field), str) or not getattr(self, field).strip():
                raise ValueError(f"{field} must be non-empty")
        for field in ("amount_units", "observed_slot"):
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field} must be non-negative integer")
        if self.amount_units == 0:
            raise ValueError("amount_units must be positive")
        identity = {"amount_units": self.amount_units, "observed_slot": self.observed_slot,
                    "schema_version": self.schema_version, "source_id": self.source_id.strip(),
                    "token_id": self.token_id.strip(), "wallet_id": self.wallet_id.strip()}
        if self.observation_id != deterministic_id("first_meaningful_swap_observation", identity):
            raise ValueError("observation_id does not match observation")


def detect_first_meaningful_swap(token_id: str, wallet_id: str, amount_units: int,
                                 observed_slot: int, source_id: str) -> FirstMeaningfulSwapObservation:
    identity = {"amount_units": amount_units, "observed_slot": observed_slot,
                "schema_version": "first_meaningful_swap_observation.v1", "source_id": source_id.strip(),
                "token_id": token_id.strip(), "wallet_id": wallet_id.strip()}
    return FirstMeaningfulSwapObservation(token_id, wallet_id, amount_units, observed_slot, source_id,
                                          deterministic_id("first_meaningful_swap_observation", identity))


__all__ = ["FirstMeaningfulSwapObservation", "detect_first_meaningful_swap"]
