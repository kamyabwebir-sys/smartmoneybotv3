from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_candidate_evidence import WalletCandidateEvidence
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_candidate_evidence_replay.v1"


@dataclass(frozen=True, slots=True)
class WalletCandidateEvidenceReplayReceipt:
    evidence_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("evidence_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet candidate evidence replay schema_version")
        if self.replay_id != deterministic_id(
            "wallet_candidate_evidence_replay", self.identity_payload()
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_wallet_candidate_evidence(
    feature: WalletCandidateFeature,
    expected: WalletCandidateEvidence,
) -> WalletCandidateEvidenceReplayReceipt:
    if not isinstance(feature, WalletCandidateFeature):
        raise TypeError("feature must be WalletCandidateFeature")
    if not isinstance(expected, WalletCandidateEvidence):
        raise TypeError("expected must be WalletCandidateEvidence")
    from smart_money.application.wallet_candidate_evidence import (
        build_wallet_candidate_evidence,
    )

    reconstructed = build_wallet_candidate_evidence(
        feature, provenance=expected.provenance
    )
    matches = reconstructed.canonical_dict() == expected.canonical_dict()
    identity = {
        "evidence_id": expected.evidence_id,
        "matches": matches,
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletCandidateEvidenceReplayReceipt(
        **identity,
        replay_id=deterministic_id("wallet_candidate_evidence_replay", identity),
    )


__all__ = [
    "WalletCandidateEvidenceReplayReceipt",
    "replay_verify_wallet_candidate_evidence",
]
