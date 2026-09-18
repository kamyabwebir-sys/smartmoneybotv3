from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.solana_candidate_replay import replay_verify_solana_candidate
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaCandidateReadRow:
    candidate: SolanaWalletTokenCandidate
    evidence_id: str
    replay_verified: bool

    def __post_init__(self) -> None:
        if not isinstance(self.candidate, SolanaWalletTokenCandidate):
            raise TypeError("candidate must be SolanaWalletTokenCandidate")
        if not isinstance(self.evidence_id, str) or not self.evidence_id.strip():
            raise ValueError("evidence_id must be non-empty")
        if not isinstance(self.replay_verified, bool):
            raise TypeError("replay_verified must be boolean")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.canonical_dict(),
            "evidence_id": self.evidence_id,
            "replay_verified": self.replay_verified,
        }


@dataclass(frozen=True, slots=True)
class SolanaCandidateReadModel:
    rows: tuple[SolanaCandidateReadRow, ...]
    model_id: str
    schema_version: str = "solana_candidate_read_model.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if not isinstance(self.model_id, str) or not self.model_id.strip():
            raise ValueError("model_id must be non-empty")
        if self.schema_version != "solana_candidate_read_model.v1":
            raise ValueError("unsupported read model schema_version")
        expected = deterministic_id(
            "solana_candidate_read_model",
            {"rows": tuple(row.canonical_dict() for row in self.rows), "schema_version": self.schema_version},
        )
        if self.model_id != expected:
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "rows": tuple(row.canonical_dict() for row in self.rows),
            "schema_version": self.schema_version,
        }


def build_solana_candidate_read_model(
    ledger: EvidenceLedger, *, verify_replay: bool = True
) -> SolanaCandidateReadModel:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if not isinstance(verify_replay, bool):
        raise TypeError("verify_replay must be boolean")
    rows: list[SolanaCandidateReadRow] = []
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "solana_wallet_token_candidate":
            continue
        data = payload.data.get("candidate")
        if not hasattr(data, "get"):
            raise ValueError("invalid candidate payload in Ledger")
        candidate = SolanaWalletTokenCandidate(
            wallet=data["wallet"], mint=data["mint"],
            activity_count=data["activity_count"], buy_count=data["buy_count"],
            first_slot=data["first_slot"], last_slot=data["last_slot"],
            reasons=tuple(data["reasons"]), candidate_id=data["candidate_id"],
            schema_version=data["schema_version"],
        )
        replay_verified = False
        if verify_replay:
            replay_verified = replay_verify_solana_candidate(candidate, ledger).matches
        rows.append(
            SolanaCandidateReadRow(
                candidate=candidate,
                evidence_id=payload.get_canonical_id(),
                replay_verified=replay_verified,
            )
        )
    rows.sort(
        key=lambda row: (
            row.candidate.first_slot,
            row.candidate.wallet,
            row.candidate.mint,
            row.candidate.candidate_id,
        )
    )
    return SolanaCandidateReadModel(
        rows=tuple(rows),
        model_id=deterministic_id(
            "solana_candidate_read_model",
            {
                "rows": tuple(row.canonical_dict() for row in rows),
                "schema_version": "solana_candidate_read_model.v1",
            },
        ),
    )


__all__ = [
    "SolanaCandidateReadModel",
    "SolanaCandidateReadRow",
    "build_solana_candidate_read_model",
]
