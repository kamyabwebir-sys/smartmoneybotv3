from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_candidate_evidence.v1"


class WalletCandidateEvidenceStatus(str, Enum):
    PROPOSED = "PROPOSED"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass(frozen=True, slots=True)
class WalletCandidateEvidence:
    feature: WalletCandidateFeature
    status: WalletCandidateEvidenceStatus
    reason_codes: tuple[str, ...]
    provenance: Mapping[str, str]
    evidence_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.feature, WalletCandidateFeature):
            raise TypeError("feature must be WalletCandidateFeature")
        if not isinstance(self.status, WalletCandidateEvidenceStatus):
            raise TypeError("status must be WalletCandidateEvidenceStatus")
        if not isinstance(self.reason_codes, tuple) or not self.reason_codes:
            raise ValueError("reason_codes must be a non-empty tuple")
        if not all(isinstance(item, str) and item.strip() for item in self.reason_codes):
            raise ValueError("reason_codes must contain non-empty text")
        if len(set(self.reason_codes)) != len(self.reason_codes):
            raise ValueError("reason_codes must be unique")
        if not isinstance(self.provenance, Mapping) or not self.provenance:
            raise ValueError("provenance must be a non-empty mapping")
        if not all(
            isinstance(key, str)
            and key.strip()
            and isinstance(value, str)
            and value.strip()
            for key, value in self.provenance.items()
        ):
            raise ValueError("provenance must contain non-empty text")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet candidate evidence schema_version")
        if self.evidence_id != deterministic_id(
            "wallet_candidate_evidence", self.identity_payload()
        ):
            raise ValueError("evidence_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "feature": self.feature.canonical_dict(),
            "provenance": dict(sorted(self.provenance.items())),
            "reason_codes": self.reason_codes,
            "schema_version": self.schema_version,
            "status": self.status.value,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"evidence_id": self.evidence_id, **self.identity_payload()}


def build_wallet_candidate_evidence(
    feature: WalletCandidateFeature,
    *,
    provenance: Mapping[str, str],
) -> WalletCandidateEvidence:
    if not isinstance(feature, WalletCandidateFeature):
        raise TypeError("feature must be WalletCandidateFeature")
    if not isinstance(provenance, Mapping) or not provenance:
        raise ValueError("provenance must be a non-empty mapping")
    reason_codes: list[str] = []
    if feature.relationship_count > 0:
        reason_codes.append("HAS_WALLET_RELATIONSHIPS")
    if feature.cohort_count > 0:
        reason_codes.append("HAS_COHORT_MEMBERSHIP")
    if feature.early_entry_consistency_bps > 0:
        reason_codes.append("HAS_EARLY_ENTRY_EVIDENCE")
    if feature.data_completeness_bps > 0:
        reason_codes.append("HAS_BEHAVIOR_PROFILE")
    status = (
        WalletCandidateEvidenceStatus.PROPOSED
        if reason_codes
        else WalletCandidateEvidenceStatus.INSUFFICIENT
    )
    if not reason_codes:
        reason_codes.append("INSUFFICIENT_CANDIDATE_EVIDENCE")
    identity = {
        "feature": feature.canonical_dict(),
        "provenance": dict(sorted(provenance.items())),
        "reason_codes": tuple(reason_codes),
        "schema_version": _SCHEMA_VERSION,
        "status": status.value,
    }
    return WalletCandidateEvidence(
        feature=feature,
        status=status,
        reason_codes=tuple(reason_codes),
        provenance=dict(sorted(provenance.items())),
        evidence_id=deterministic_id("wallet_candidate_evidence", identity),
    )


__all__ = [
    "WalletCandidateEvidence",
    "WalletCandidateEvidenceStatus",
    "build_wallet_candidate_evidence",
]
