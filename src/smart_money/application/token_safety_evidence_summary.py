from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.token_safety_rule_evaluation import (
    TokenSafetyRuleEvaluation,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "token_safety_evidence_summary.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetyEvidenceSummary:
    observation_id: str
    total_rules: int
    triggered_rules: int
    triggered_rule_ids: tuple[str, ...]
    triggered_reasons: tuple[str, ...]
    summary_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.observation_id, str) or not self.observation_id.strip():
            raise ValueError("observation_id must be non-empty")
        for name in ("total_rules", "triggered_rules"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.triggered_rules > self.total_rules:
            raise ValueError("triggered_rules cannot exceed total_rules")
        if not isinstance(self.triggered_rule_ids, tuple) or not isinstance(
            self.triggered_reasons, tuple
        ):
            raise TypeError("triggered rule fields must be tuples")
        if len(self.triggered_rule_ids) != self.triggered_rules:
            raise ValueError("triggered_rule_ids count does not match triggered_rules")
        if len(self.triggered_reasons) != self.triggered_rules:
            raise ValueError("triggered_reasons count does not match triggered_rules")
        if not all(isinstance(item, str) and item.strip() for item in self.triggered_rule_ids):
            raise ValueError("triggered_rule_ids must contain non-empty text")
        if not all(isinstance(item, str) and item.strip() for item in self.triggered_reasons):
            raise ValueError("triggered_reasons must contain non-empty text")
        if not isinstance(self.summary_id, str) or not self.summary_id.strip():
            raise ValueError("summary_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported evidence summary schema_version")
        if self.summary_id != deterministic_id(
            "token_safety_evidence_summary", self.identity_payload()
        ):
            raise ValueError("summary_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "schema_version": self.schema_version,
            "total_rules": self.total_rules,
            "triggered_reasons": self.triggered_reasons,
            "triggered_rule_ids": self.triggered_rule_ids,
            "triggered_rules": self.triggered_rules,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"summary_id": self.summary_id, **self.identity_payload()}


def summarize_token_safety_evidence(
    evaluations: tuple[TokenSafetyRuleEvaluation, ...] | list[TokenSafetyRuleEvaluation],
) -> TokenSafetyEvidenceSummary:
    values = tuple(evaluations)
    if not values:
        raise ValueError("evaluations must be non-empty")
    if not all(isinstance(item, TokenSafetyRuleEvaluation) for item in values):
        raise TypeError("evaluations must contain TokenSafetyRuleEvaluation values")
    observation_ids = {item.observation_id for item in values}
    if len(observation_ids) != 1:
        raise ValueError("evaluations must belong to one observation")
    ordered = tuple(sorted(values, key=lambda item: item.rule_id))
    triggered = tuple(item for item in ordered if item.triggered)
    identity = {
        "observation_id": ordered[0].observation_id,
        "schema_version": _SCHEMA_VERSION,
        "total_rules": len(ordered),
        "triggered_reasons": tuple(item.reason for item in triggered),
        "triggered_rule_ids": tuple(item.rule_id for item in triggered),
        "triggered_rules": len(triggered),
    }
    return TokenSafetyEvidenceSummary(
        observation_id=ordered[0].observation_id,
        total_rules=len(ordered),
        triggered_rules=len(triggered),
        triggered_rule_ids=identity["triggered_rule_ids"],
        triggered_reasons=identity["triggered_reasons"],
        summary_id=deterministic_id("token_safety_evidence_summary", identity),
    )


__all__ = ["TokenSafetyEvidenceSummary", "summarize_token_safety_evidence"]
