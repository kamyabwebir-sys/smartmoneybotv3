from __future__ import annotations
from smart_money.application.token_safety_candidate_summary_read_model import (
    TokenSafetyCandidateSummaryReadModel,
    build_token_safety_candidate_summary_read_model,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger

def build_token_safety_candidate_read_model(
    ledger: EvidenceLedger, *, verify_replay: bool = True
) -> TokenSafetyCandidateSummaryReadModel:
    return build_token_safety_candidate_summary_read_model(ledger, verify_replay=verify_replay)

__all__ = ["build_token_safety_candidate_read_model"]
