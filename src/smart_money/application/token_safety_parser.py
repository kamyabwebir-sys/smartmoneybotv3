from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from smart_money.core.ids import deterministic_id
from smart_money.domain.token_safety import TokenSafetyObservation


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value.strip()


def _optional_text(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _text(value, name)


def _non_negative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def parse_token_safety_observation(
    raw: Mapping[str, Any],
) -> TokenSafetyObservation:
    """Parse a canonical raw Token Safety mapping without producing a verdict."""
    if not isinstance(raw, Mapping):
        raise TypeError("raw token safety observation must be a mapping")
    allowed = {
        "token",
        "observed_at",
        "mint_authority",
        "freeze_authority",
        "update_authority",
        "liquidity_amount",
        "holder_concentration_bps",
        "deployer",
    }
    if set(raw) != allowed:
        raise ValueError("raw token safety keys do not match schema")
    values = {
        "deployer": _text(raw["deployer"], "deployer"),
        "freeze_authority": _optional_text(raw["freeze_authority"], "freeze_authority"),
        "holder_concentration_bps": _non_negative_int(raw["holder_concentration_bps"], "holder_concentration_bps"),
        "liquidity_amount": _non_negative_int(raw["liquidity_amount"], "liquidity_amount"),
        "mint": _optional_text(raw["mint_authority"], "mint_authority"),
        "observed_at": _non_negative_int(raw["observed_at"], "observed_at"),
        "schema_version": "token_safety_observation.v1",
        "token": _text(raw["token"], "token"),
        "update_authority": _optional_text(raw["update_authority"], "update_authority"),
    }
    return TokenSafetyObservation(
        token=values["token"], observed_at=values["observed_at"],
        mint_authority=values["mint"], freeze_authority=values["freeze_authority"],
        update_authority=values["update_authority"],
        liquidity_amount=values["liquidity_amount"],
        holder_concentration_bps=values["holder_concentration_bps"],
        deployer=values["deployer"],
        observation_id=deterministic_id("token_safety_observation", values),
    )


__all__ = ["parse_token_safety_observation"]
