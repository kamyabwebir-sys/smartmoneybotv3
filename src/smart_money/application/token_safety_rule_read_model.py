from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.token_safety_rule_evaluation import TokenSafetyRuleEvaluation
from smart_money.application.token_safety_rule_replay import replay_verify_token_safety_rule_evaluation
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class TokenSafetyRuleReadRow:
    evaluation: TokenSafetyRuleEvaluation
    evidence_id: str
    replay_verified: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "evaluation": self.evaluation.canonical_dict(),
            "evidence_id": self.evidence_id,
            "replay_verified": self.replay_verified,
        }


@dataclass(frozen=True, slots=True)
class TokenSafetyRuleReadModel:
    rows: tuple[TokenSafetyRuleReadRow, ...]
    model_id: str
    schema_version: str = "token_safety_rule_read_model.v1"

    def __post_init__(self) -> None:
        expected = deterministic_id(
            "token_safety_rule_read_model",
            {"rows": tuple(row.canonical_dict() for row in self.rows), "schema_version": self.schema_version},
        )
        if self.model_id != expected:
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "rows": tuple(row.canonical_dict() for row in self.rows),
            "schema_version": self.schema_version,
        }


def build_token_safety_rule_read_model(
    ledger: EvidenceLedger, *, verify_replay: bool = True
) -> TokenSafetyRuleReadModel:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if not isinstance(verify_replay, bool):
        raise TypeError("verify_replay must be boolean")
    rows: list[TokenSafetyRuleReadRow] = []
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "token_safety_rule_evaluation":
            continue
        data = payload.data.get("evaluation")
        if not hasattr(data, "get"):
            raise ValueError("invalid rule evaluation payload in Ledger")
        evaluation = TokenSafetyRuleEvaluation(
            observation_id=data["observation_id"],
            rule_id=data["rule_id"],
            triggered=data["triggered"],
            reason=data["reason"],
            evaluation_id=data["evaluation_id"],
            schema_version=data["schema_version"],
        )
        replay_verified = (
            replay_verify_token_safety_rule_evaluation(evaluation, ledger).matches
            if verify_replay
            else False
        )
        rows.append(
            TokenSafetyRuleReadRow(
                evaluation=evaluation,
                evidence_id=payload.get_canonical_id(),
                replay_verified=replay_verified,
            )
        )
    rows.sort(
        key=lambda row: (
            row.evaluation.observation_id,
            row.evaluation.rule_id,
            row.evaluation.evaluation_id,
        )
    )
    identity = {
        "rows": tuple(row.canonical_dict() for row in rows),
        "schema_version": "token_safety_rule_read_model.v1",
    }
    return TokenSafetyRuleReadModel(
        rows=tuple(rows),
        model_id=deterministic_id("token_safety_rule_read_model", identity),
    )


__all__ = ["TokenSafetyRuleReadModel", "TokenSafetyRuleReadRow", "build_token_safety_rule_read_model"]
