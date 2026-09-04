from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.token_safety_evidence_summary import TokenSafetyEvidenceSummary
from smart_money.application.token_safety_summary_replay import (
    replay_verify_token_safety_evidence_summary,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class TokenSafetySummaryReadRow:
    summary: TokenSafetyEvidenceSummary
    evidence_id: str
    replay_verified: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "replay_verified": self.replay_verified,
            "summary": self.summary.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class TokenSafetySummaryReadModel:
    rows: tuple[TokenSafetySummaryReadRow, ...]
    model_id: str
    schema_version: str = "token_safety_summary_read_model.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if self.model_id != deterministic_id(
            "token_safety_summary_read_model",
            {"rows": tuple(row.canonical_dict() for row in self.rows), "schema_version": self.schema_version},
        ):
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "rows": tuple(row.canonical_dict() for row in self.rows),
            "schema_version": self.schema_version,
        }


def build_token_safety_summary_read_model(
    ledger: EvidenceLedger, *, verify_replay: bool = True
) -> TokenSafetySummaryReadModel:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if not isinstance(verify_replay, bool):
        raise TypeError("verify_replay must be boolean")
    rows: list[TokenSafetySummaryReadRow] = []
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "token_safety_evidence_summary":
            continue
        data = payload.data.get("summary")
        if not hasattr(data, "get"):
            raise ValueError("invalid token safety summary payload in Ledger")
        summary = TokenSafetyEvidenceSummary(
            observation_id=data["observation_id"],
            total_rules=data["total_rules"],
            triggered_rules=data["triggered_rules"],
            triggered_rule_ids=tuple(data["triggered_rule_ids"]),
            triggered_reasons=tuple(data["triggered_reasons"]),
            summary_id=data["summary_id"],
            schema_version=data["schema_version"],
        )
        replay_verified = (
            replay_verify_token_safety_evidence_summary(summary, ledger).matches
            if verify_replay
            else False
        )
        rows.append(
            TokenSafetySummaryReadRow(
                summary=summary,
                evidence_id=payload.get_canonical_id(),
                replay_verified=replay_verified,
            )
        )
    rows.sort(key=lambda row: (row.summary.observation_id, row.summary.summary_id))
    identity = {
        "rows": tuple(row.canonical_dict() for row in rows),
        "schema_version": "token_safety_summary_read_model.v1",
    }
    return TokenSafetySummaryReadModel(
        rows=tuple(rows),
        model_id=deterministic_id("token_safety_summary_read_model", identity),
    )


__all__ = [
    "TokenSafetySummaryReadModel",
    "TokenSafetySummaryReadRow",
    "build_token_safety_summary_read_model",
]
