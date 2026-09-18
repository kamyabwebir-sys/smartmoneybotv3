from __future__ import annotations
from dataclasses import dataclass
from smart_money.application.token_safety_evidence_summary import TokenSafetyEvidenceSummary
from smart_money.application.token_safety_summary_store import TokenSafetySummaryStore
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class TokenSafetySummaryStoreReplayVerification:
    summary_id: str
    matches: bool
    verification_id: str
    schema_version: str = "token_safety_summary_store_replay.v1"

def verify_token_safety_summary_store(summary: TokenSafetyEvidenceSummary,
                                      store: TokenSafetySummaryStore) -> TokenSafetySummaryStoreReplayVerification:
    if not isinstance(summary, TokenSafetyEvidenceSummary) or not isinstance(store, TokenSafetySummaryStore):
        raise TypeError("summary and store types are invalid")
    matches = store.get(summary.summary_id) == summary
    identity = {"summary_id": summary.summary_id, "matches": matches,
                "schema_version": "token_safety_summary_store_replay.v1"}
    return TokenSafetySummaryStoreReplayVerification(summary.summary_id, matches,
        deterministic_id("token_safety_summary_store_replay", identity))

__all__ = ["TokenSafetySummaryStoreReplayVerification", "verify_token_safety_summary_store"]
