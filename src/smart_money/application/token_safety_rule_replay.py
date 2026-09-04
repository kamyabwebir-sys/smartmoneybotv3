from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.token_safety_rule_evaluation import TokenSafetyRuleEvaluation
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "token_safety_rule_replay.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetyRuleReplayReceipt:
    evaluation_id: str
    evidence_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("evaluation_id", "evidence_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported rule replay schema_version")
        if self.replay_id != deterministic_id(
            "token_safety_rule_replay", self.identity_payload()
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "evidence_id": self.evidence_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_token_safety_rule_evaluation(
    evaluation: TokenSafetyRuleEvaluation, ledger: EvidenceLedger
) -> TokenSafetyRuleReplayReceipt:
    if not isinstance(evaluation, TokenSafetyRuleEvaluation):
        raise TypeError("evaluation must be TokenSafetyRuleEvaluation")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    retained = None
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "token_safety_rule_evaluation":
            continue
        data = payload.data.get("evaluation")
        if not hasattr(data, "get"):
            raise ValueError("invalid rule evaluation payload in Ledger")
        if data.get("evaluation_id") == evaluation.evaluation_id:
            retained = payload
            break
    if retained is None:
        raise ValueError("persisted token safety rule evidence is missing")
    data = retained.data["evaluation"]
    if dict(data) != evaluation.canonical_dict():
        raise ValueError("persisted token safety rule does not match source")
    evidence_id = retained.get_canonical_id()
    return TokenSafetyRuleReplayReceipt(
        evaluation_id=evaluation.evaluation_id,
        evidence_id=evidence_id,
        matches=True,
        replay_id=deterministic_id(
            "token_safety_rule_replay",
            {
                "evaluation_id": evaluation.evaluation_id,
                "evidence_id": evidence_id,
                "matches": True,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = [
    "TokenSafetyRuleReplayReceipt",
    "replay_verify_token_safety_rule_evaluation",
]
