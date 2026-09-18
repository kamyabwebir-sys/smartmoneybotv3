from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaCandidateReplayReceipt:
    candidate_id: str
    evidence_id: str
    matches: bool
    replay_id: str
    schema_version: str = "solana_candidate_replay.v1"

    def __post_init__(self) -> None:
        for name in ("candidate_id", "evidence_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != "solana_candidate_replay.v1":
            raise ValueError("unsupported candidate replay schema_version")
        expected = deterministic_id("solana_candidate_replay", self.identity_payload())
        if self.replay_id != expected:
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "evidence_id": self.evidence_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_solana_candidate(
    candidate: SolanaWalletTokenCandidate, ledger: EvidenceLedger
) -> SolanaCandidateReplayReceipt:
    if not isinstance(candidate, SolanaWalletTokenCandidate):
        raise TypeError("candidate must be SolanaWalletTokenCandidate")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    expected_evidence_id: str | None = None
    retained: SolanaWalletTokenCandidate | None = None
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "solana_wallet_token_candidate":
            continue
        data = payload.data.get("candidate")
        if not hasattr(data, "get"):
            raise ValueError("invalid candidate payload in Ledger")
        parsed = SolanaWalletTokenCandidate(
            wallet=data["wallet"], mint=data["mint"],
            activity_count=data["activity_count"], buy_count=data["buy_count"],
            first_slot=data["first_slot"], last_slot=data["last_slot"],
            reasons=tuple(data["reasons"]), candidate_id=data["candidate_id"],
            schema_version=data["schema_version"],
        )
        if parsed.candidate_id == candidate.candidate_id:
            expected_evidence_id = payload.get_canonical_id()
            retained = parsed
            break
    if retained is None or expected_evidence_id is None:
        raise ValueError("persisted candidate evidence is missing")
    if retained.canonical_dict() != candidate.canonical_dict():
        raise ValueError("persisted candidate does not match replay input")
    identity = {
        "candidate_id": candidate.candidate_id,
        "evidence_id": expected_evidence_id,
        "matches": True,
        "schema_version": "solana_candidate_replay.v1",
    }
    return SolanaCandidateReplayReceipt(
        candidate_id=candidate.candidate_id,
        evidence_id=expected_evidence_id,
        matches=True,
        replay_id=deterministic_id("solana_candidate_replay", identity),
    )


__all__ = ["SolanaCandidateReplayReceipt", "replay_verify_solana_candidate"]
