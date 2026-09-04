from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.token_safety_rule_evaluation import TokenSafetyRuleEvaluation
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "token_safety_rule_ledger.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetyRuleLedgerReceipt:
    receipt_id: str
    evaluation_id: str
    evidence_id: str
    ledger_entry_count: int
    already_present: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("receipt_id", "evaluation_id", "evidence_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if (
            isinstance(self.ledger_entry_count, bool)
            or not isinstance(self.ledger_entry_count, int)
            or self.ledger_entry_count < 0
        ):
            raise ValueError("ledger_entry_count must be non-negative integer")
        if not isinstance(self.already_present, bool):
            raise TypeError("already_present must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported rule ledger schema_version")
        if self.receipt_id != deterministic_id(
            "token_safety_rule_ledger", self.identity_payload()
        ):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "already_present": self.already_present,
            "evidence_id": self.evidence_id,
            "evaluation_id": self.evaluation_id,
            "ledger_entry_count": self.ledger_entry_count,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def ingest_token_safety_rule_evaluation(
    evaluation: TokenSafetyRuleEvaluation, ledger: EvidenceLedger
) -> TokenSafetyRuleLedgerReceipt:
    if not isinstance(evaluation, TokenSafetyRuleEvaluation):
        raise TypeError("evaluation must be TokenSafetyRuleEvaluation")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="token_safety",
        evidence_type="token_safety_rule_evaluation",
        timestamp=0,
        data={"evaluation": evaluation.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
            "provenance": {
                "evaluation_id": evaluation.evaluation_id,
                "observation_id": evaluation.observation_id,
                "rule_id": evaluation.rule_id,
                "source_id": "token_safety",
                "source_schema_version": evaluation.schema_version,
            },
        },
    )
    evidence_id = payload.get_canonical_id()
    already_present = ledger.contains(evidence_id)
    before_count = ledger.entry_count
    if ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained rule evaluation payload mismatch")
    expected_count = before_count if already_present else before_count + 1
    if ledger.entry_count != expected_count:
        raise ValueError("Ledger entry count violates idempotent append contract")
    identity = {
        "already_present": already_present,
        "evidence_id": evidence_id,
        "evaluation_id": evaluation.evaluation_id,
        "ledger_entry_count": ledger.entry_count,
        "schema_version": _SCHEMA_VERSION,
    }
    return TokenSafetyRuleLedgerReceipt(
        receipt_id=deterministic_id("token_safety_rule_ledger", identity),
        evaluation_id=evaluation.evaluation_id,
        evidence_id=evidence_id,
        ledger_entry_count=ledger.entry_count,
        already_present=already_present,
    )


__all__ = ["TokenSafetyRuleLedgerReceipt", "ingest_token_safety_rule_evaluation"]
