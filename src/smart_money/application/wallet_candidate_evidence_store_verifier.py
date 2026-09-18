from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.wallet_candidate_evidence_store import (
    JsonWalletCandidateEvidenceStore,
)
from smart_money.application.wallet_candidate_evidence import WalletCandidateEvidence
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_candidate_evidence_store_verifier.v1"


@dataclass(frozen=True, slots=True)
class WalletCandidateEvidenceStoreVerificationReceipt:
    evidence_id: str
    matches: bool
    verification_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("evidence_id", "verification_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet candidate evidence store verifier schema_version")
        if self.verification_id != deterministic_id(
            "wallet_candidate_evidence_store_verification", self.identity_payload()
        ):
            raise ValueError("verification_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"verification_id": self.verification_id, **self.identity_payload()}


def verify_wallet_candidate_evidence_store(
    store: JsonWalletCandidateEvidenceStore,
    expected: WalletCandidateEvidence,
) -> WalletCandidateEvidenceStoreVerificationReceipt:
    if not isinstance(store, JsonWalletCandidateEvidenceStore):
        raise TypeError("store must be JsonWalletCandidateEvidenceStore")
    if not isinstance(expected, WalletCandidateEvidence):
        raise TypeError("expected must be WalletCandidateEvidence")
    retained = store.get(expected.evidence_id)
    if retained is None:
        raise ValueError("expected wallet candidate evidence is missing from Store")
    if retained.canonical_dict() != expected.canonical_dict():
        raise ValueError("stored wallet candidate evidence does not match expected")
    identity = {
        "evidence_id": expected.evidence_id,
        "matches": True,
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletCandidateEvidenceStoreVerificationReceipt(
        **identity,
        verification_id=deterministic_id(
            "wallet_candidate_evidence_store_verification", identity
        ),
    )


__all__ = [
    "WalletCandidateEvidenceStoreVerificationReceipt",
    "verify_wallet_candidate_evidence_store",
]
