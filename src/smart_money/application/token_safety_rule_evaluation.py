from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id
from smart_money.domain.token_safety import TokenSafetyObservation


@dataclass(frozen=True, slots=True)
class TokenSafetyRuleEvaluation:
    observation_id: str
    rule_id: str
    triggered: bool
    reason: str
    evaluation_id: str
    schema_version: str = "token_safety_rule_evaluation.v1"

    def __post_init__(self) -> None:
        for name in ("observation_id", "rule_id", "reason", "evaluation_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.triggered, bool):
            raise TypeError("triggered must be boolean")
        if self.schema_version != "token_safety_rule_evaluation.v1":
            raise ValueError("unsupported rule evaluation schema_version")
        if self.evaluation_id != deterministic_id(
            "token_safety_rule_evaluation", self.identity_payload()
        ):
            raise ValueError("evaluation_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "reason": self.reason,
            "rule_id": self.rule_id,
            "schema_version": self.schema_version,
            "triggered": self.triggered,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"evaluation_id": self.evaluation_id, **self.identity_payload()}


def evaluate_token_safety_rules(
    observation: TokenSafetyObservation,
    *,
    min_liquidity_amount: int = 1,
    max_holder_concentration_bps: int = 5000,
) -> tuple[TokenSafetyRuleEvaluation, ...]:
    if not isinstance(observation, TokenSafetyObservation):
        raise TypeError("observation must be TokenSafetyObservation")
    if (
        isinstance(min_liquidity_amount, bool)
        or not isinstance(min_liquidity_amount, int)
        or min_liquidity_amount < 0
    ):
        raise ValueError("min_liquidity_amount must be a non-negative integer")
    if (
        isinstance(max_holder_concentration_bps, bool)
        or not isinstance(max_holder_concentration_bps, int)
        or not 0 <= max_holder_concentration_bps <= 10000
    ):
        raise ValueError("max_holder_concentration_bps must be between 0 and 10000")
    checks = (
        (
            "authority.active",
            any(
                value is not None
                for value in (
                    observation.mint_authority,
                    observation.freeze_authority,
                    observation.update_authority,
                )
            ),
            "one or more token authorities are present",
        ),
        (
            "liquidity.below_threshold",
            observation.liquidity_amount < min_liquidity_amount,
            f"liquidity_amount={observation.liquidity_amount} threshold={min_liquidity_amount}",
        ),
        (
            "concentration.above_threshold",
            observation.holder_concentration_bps > max_holder_concentration_bps,
            f"holder_concentration_bps={observation.holder_concentration_bps} threshold={max_holder_concentration_bps}",
        ),
        (
            "deployer.observed",
            bool(observation.deployer.strip()),
            "deployer identity is present in observation",
        ),
    )
    result = []
    for rule_id, triggered, reason in checks:
        identity = {
            "observation_id": observation.observation_id,
            "reason": reason,
            "rule_id": rule_id,
            "schema_version": "token_safety_rule_evaluation.v1",
            "triggered": triggered,
        }
        result.append(
            TokenSafetyRuleEvaluation(
                observation_id=observation.observation_id,
                rule_id=rule_id,
                triggered=triggered,
                reason=reason,
                evaluation_id=deterministic_id(
                    "token_safety_rule_evaluation", identity
                ),
            )
        )
    return tuple(result)


__all__ = ["TokenSafetyRuleEvaluation", "evaluate_token_safety_rules"]
