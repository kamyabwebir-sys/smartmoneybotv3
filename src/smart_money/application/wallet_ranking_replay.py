from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_candidate_evidence import WalletCandidateEvidence
from smart_money.application.wallet_ranking import WalletRanking, rank_wallet_candidates
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_ranking_replay.v1"


@dataclass(frozen=True, slots=True)
class WalletRankingReplayReceipt:
    ranking_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("ranking_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet ranking replay schema_version")
        if self.replay_id != deterministic_id(
            "wallet_ranking_replay", self.identity_payload()
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "ranking_id": self.ranking_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_wallet_ranking(
    evidence: tuple[WalletCandidateEvidence, ...],
    expected: WalletRanking,
) -> WalletRankingReplayReceipt:
    if not isinstance(evidence, tuple) or not all(
        isinstance(item, WalletCandidateEvidence) for item in evidence
    ):
        raise TypeError("evidence must be tuple of WalletCandidateEvidence")
    if not isinstance(expected, WalletRanking):
        raise TypeError("expected must be WalletRanking")
    reconstructed = rank_wallet_candidates(evidence)
    matches = reconstructed.canonical_dict() == expected.canonical_dict()
    identity = {
        "matches": matches,
        "ranking_id": expected.ranking_id,
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletRankingReplayReceipt(
        **identity,
        replay_id=deterministic_id("wallet_ranking_replay", identity),
    )


__all__ = ["WalletRankingReplayReceipt", "replay_verify_wallet_ranking"]
