from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.first_liquidity_detection import FirstLiquidityObservation
from smart_money.application.token_lifecycle import (
    TokenLifecycle,
    TokenLifecycleState,
    advance_token_lifecycle,
    build_token_lifecycle,
)
from smart_money.application.token_metadata_observation import TokenMetadataObservation
from smart_money.application.first_meaningful_swap import FirstMeaningfulSwapObservation


@dataclass(frozen=True, slots=True)
class TokenLifecycleObservationBinding:
    lifecycle: TokenLifecycle
    observation_ids: tuple[str, ...]
    schema_version: str = "token_lifecycle_observation_binding.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.lifecycle, TokenLifecycle):
            raise TypeError("lifecycle must be TokenLifecycle")
        if not isinstance(self.observation_ids, tuple) or not self.observation_ids:
            raise ValueError("observation_ids must be non-empty tuple")
        if any(not isinstance(item, str) or not item.strip() for item in self.observation_ids):
            raise ValueError("observation_ids must contain non-empty strings")
        if self.schema_version != "token_lifecycle_observation_binding.v1":
            raise ValueError("unsupported schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "lifecycle": self.lifecycle.canonical_dict(),
            "observation_ids": list(self.observation_ids),
            "schema_version": self.schema_version,
        }


def bind_token_metadata_observation(observation: TokenMetadataObservation) -> TokenLifecycleObservationBinding:
    if not isinstance(observation, TokenMetadataObservation):
        raise TypeError("observation must be TokenMetadataObservation")
    lifecycle = build_token_lifecycle(
        observation.token_id, TokenLifecycleState.METADATA_OBSERVED,
        observation.observed_slot, (observation.observation_id,),
    )
    return TokenLifecycleObservationBinding(lifecycle, (observation.observation_id,))


def bind_first_liquidity_observation(
    observation: FirstLiquidityObservation,
    current: TokenLifecycle | None = None,
) -> TokenLifecycleObservationBinding:
    if not isinstance(observation, FirstLiquidityObservation):
        raise TypeError("observation must be FirstLiquidityObservation")
    lifecycle = (
        build_token_lifecycle(observation.token_id, TokenLifecycleState.FIRST_LIQUIDITY,
                              observation.observed_slot, (observation.observation_id,))
        if current is None
        else advance_token_lifecycle(
            current, state=TokenLifecycleState.FIRST_LIQUIDITY,
            observed_slot=observation.observed_slot,
            evidence_ids=(*current.evidence_ids, observation.observation_id),
        )
    )
    return TokenLifecycleObservationBinding(lifecycle, lifecycle.evidence_ids)


def bind_first_meaningful_swap_observation(
    observation: FirstMeaningfulSwapObservation, current: TokenLifecycle
) -> TokenLifecycleObservationBinding:
    if not isinstance(observation, FirstMeaningfulSwapObservation):
        raise TypeError("observation must be FirstMeaningfulSwapObservation")
    if observation.token_id.strip() != current.token_id.strip():
        raise ValueError("token_id mismatch")
    lifecycle = advance_token_lifecycle(
        current,
        state=TokenLifecycleState.FIRST_MEANINGFUL_SWAP,
        observed_slot=observation.observed_slot,
        evidence_ids=(*current.evidence_ids, observation.observation_id),
    )
    return TokenLifecycleObservationBinding(lifecycle, lifecycle.evidence_ids)


__all__ = ["TokenLifecycleObservationBinding", "bind_first_liquidity_observation", "bind_token_metadata_observation", "bind_first_meaningful_swap_observation"]
