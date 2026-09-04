from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_candidate_evidence import WalletCandidateEvidence
from smart_money.application.wallet_candidate_evidence_replay import (
    WalletCandidateEvidenceReplayReceipt,
)
from smart_money.application.wallet_candidate_evidence_store_verifier import (
    WalletCandidateEvidenceStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_candidate_evidence_audit.v1"


@dataclass(frozen=True, slots=True)
class WalletCandidateEvidenceAuditReceipt:
    evidence_id: str
    replay_id: str
    store_verification_id: str
    replay_matches: bool
    audit_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "evidence_id",
            "replay_id",
            "store_verification_id",
            "audit_id",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.replay_matches, bool):
            raise TypeError("replay_matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet candidate evidence audit schema_version")
        if self.audit_id != deterministic_id(
            "wallet_candidate_evidence_audit", self.identity_payload()
        ):
            raise ValueError("audit_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "replay_id": self.replay_id,
            "replay_matches": self.replay_matches,
            "schema_version": self.schema_version,
            "store_verification_id": self.store_verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"audit_id": self.audit_id, **self.identity_payload()}


def build_wallet_candidate_evidence_audit_receipt(
    *,
    evidence: WalletCandidateEvidence,
    replay_receipt: WalletCandidateEvidenceReplayReceipt,
    store_verification: WalletCandidateEvidenceStoreVerificationReceipt,
) -> WalletCandidateEvidenceAuditReceipt:
    if not isinstance(evidence, WalletCandidateEvidence):
        raise TypeError("evidence must be WalletCandidateEvidence")
    if not isinstance(replay_receipt, WalletCandidateEvidenceReplayReceipt):
        raise TypeError("replay_receipt must be WalletCandidateEvidenceReplayReceipt")
    if not isinstance(
        store_verification, WalletCandidateEvidenceStoreVerificationReceipt
    ):
        raise TypeError(
            "store_verification must be WalletCandidateEvidenceStoreVerificationReceipt"
        )
    if replay_receipt.evidence_id != evidence.evidence_id:
        raise ValueError("replay receipt evidence_id mismatch")
    if store_verification.evidence_id != evidence.evidence_id:
        raise ValueError("store verification evidence_id mismatch")
    identity = {
        "evidence_id": evidence.evidence_id,
        "replay_id": replay_receipt.replay_id,
        "replay_matches": replay_receipt.matches and store_verification.matches,
        "schema_version": _SCHEMA_VERSION,
        "store_verification_id": store_verification.verification_id,
    }
    return WalletCandidateEvidenceAuditReceipt(
        **identity,
        audit_id=deterministic_id("wallet_candidate_evidence_audit", identity),
    )


__all__ = [
    "WalletCandidateEvidenceAuditReceipt",
    "build_wallet_candidate_evidence_audit_receipt",
]
