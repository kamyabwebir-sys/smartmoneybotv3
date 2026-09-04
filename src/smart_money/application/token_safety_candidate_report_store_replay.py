from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.token_safety_candidate_report_store import (
    JsonTokenSafetyCandidateEvidenceReportStore,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.token_safety_candidate_report import (
    TokenSafetyCandidateEvidenceReport,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "token_safety_candidate_evidence_report_store_replay.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetyCandidateReportStoreReplayReceipt:
    report_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("report_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported report store replay schema_version")
        expected = deterministic_id(
            "token_safety_candidate_evidence_report_store_replay",
            self.identity_payload(),
        )
        if self.replay_id != expected:
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "report_id": self.report_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_token_safety_candidate_report_store(
    store: JsonTokenSafetyCandidateEvidenceReportStore,
    expected: TokenSafetyCandidateEvidenceReport,
    ledger: EvidenceLedger,
) -> TokenSafetyCandidateReportStoreReplayReceipt:
    if not isinstance(store, JsonTokenSafetyCandidateEvidenceReportStore):
        raise TypeError("store must be JsonTokenSafetyCandidateEvidenceReportStore")
    if not isinstance(expected, TokenSafetyCandidateEvidenceReport):
        raise TypeError("expected must be TokenSafetyCandidateEvidenceReport")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    persisted = store.load()
    if persisted is None:
        raise ValueError("persisted token safety candidate report is missing")
    if persisted.canonical_dict() != expected.canonical_dict():
        raise ValueError("persisted token safety candidate report does not match expected")
    return TokenSafetyCandidateReportStoreReplayReceipt(
        report_id=expected.report_id,
        matches=True,
        replay_id=deterministic_id(
            "token_safety_candidate_evidence_report_store_replay",
            {
                "matches": True,
                "report_id": expected.report_id,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = [
    "TokenSafetyCandidateReportStoreReplayReceipt",
    "replay_verify_token_safety_candidate_report_store",
]
