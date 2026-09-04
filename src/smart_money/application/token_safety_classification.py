from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from smart_money.core.ids import deterministic_id
from smart_money.domain.token_safety import TokenSafetyObservation


class TokenSafetyEvidenceCategory(str, Enum):
    AUTHORITY = "AUTHORITY"
    LIQUIDITY = "LIQUIDITY"
    CONCENTRATION = "CONCENTRATION"
    DEPLOYER = "DEPLOYER"


@dataclass(frozen=True, slots=True)
class TokenSafetyEvidenceClassification:
    observation_id: str
    category: TokenSafetyEvidenceCategory
    reason: str
    classification_id: str
    schema_version: str = "token_safety_evidence_classification.v1"

    def __post_init__(self) -> None:
        for name in ("observation_id", "reason", "classification_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.category, TokenSafetyEvidenceCategory):
            raise TypeError("category must be TokenSafetyEvidenceCategory")
        if self.schema_version != "token_safety_evidence_classification.v1":
            raise ValueError("unsupported classification schema_version")
        expected = deterministic_id(
            "token_safety_evidence_classification",
            {
                "category": self.category.value,
                "observation_id": self.observation_id,
                "reason": self.reason,
                "schema_version": self.schema_version,
            },
        )
        if self.classification_id != expected:
            raise ValueError("classification_id does not match deterministic payload")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "classification_id": self.classification_id,
            "observation_id": self.observation_id,
            "reason": self.reason,
            "schema_version": self.schema_version,
        }


def classify_token_safety_evidence(
    observation: TokenSafetyObservation,
) -> tuple[TokenSafetyEvidenceClassification, ...]:
    if not isinstance(observation, TokenSafetyObservation):
        raise TypeError("observation must be TokenSafetyObservation")
    facts = (
        (
            TokenSafetyEvidenceCategory.AUTHORITY,
            "authority fields are part of token safety evidence",
        ),
        (
            TokenSafetyEvidenceCategory.LIQUIDITY,
            f"liquidity_amount={observation.liquidity_amount}",
        ),
        (
            TokenSafetyEvidenceCategory.CONCENTRATION,
            f"holder_concentration_bps={observation.holder_concentration_bps}",
        ),
        (
            TokenSafetyEvidenceCategory.DEPLOYER,
            f"deployer={observation.deployer}",
        ),
    )
    result = []
    for category, reason in facts:
        identity = {
            "category": category.value,
            "observation_id": observation.observation_id,
            "reason": reason,
            "schema_version": "token_safety_evidence_classification.v1",
        }
        result.append(
            TokenSafetyEvidenceClassification(
                observation_id=observation.observation_id,
                category=category,
                reason=reason,
                classification_id=deterministic_id(
                    "token_safety_evidence_classification", identity
                ),
            )
        )
    return tuple(result)


__all__ = [
    "TokenSafetyEvidenceCategory",
    "TokenSafetyEvidenceClassification",
    "classify_token_safety_evidence",
]
