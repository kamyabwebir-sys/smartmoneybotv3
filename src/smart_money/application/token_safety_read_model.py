from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.token_safety_replay import (
    replay_verify_token_safety_observation,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.token_safety import TokenSafetyObservation


@dataclass(frozen=True, slots=True)
class TokenSafetyReadRow:
    observation: TokenSafetyObservation
    evidence_id: str
    replay_verified: bool

    def __post_init__(self) -> None:
        if not isinstance(self.observation, TokenSafetyObservation):
            raise TypeError("observation must be TokenSafetyObservation")
        if not isinstance(self.evidence_id, str) or not self.evidence_id.strip():
            raise ValueError("evidence_id must be non-empty")
        if not isinstance(self.replay_verified, bool):
            raise TypeError("replay_verified must be boolean")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "observation": self.observation.canonical_dict(),
            "replay_verified": self.replay_verified,
        }


@dataclass(frozen=True, slots=True)
class TokenSafetyReadModel:
    rows: tuple[TokenSafetyReadRow, ...]
    model_id: str
    schema_version: str = "token_safety_read_model.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if not isinstance(self.model_id, str) or not self.model_id.strip():
            raise ValueError("model_id must be non-empty")
        if self.schema_version != "token_safety_read_model.v1":
            raise ValueError("unsupported read model schema_version")
        expected = deterministic_id(
            "token_safety_read_model",
            {
                "rows": tuple(row.canonical_dict() for row in self.rows),
                "schema_version": self.schema_version,
            },
        )
        if self.model_id != expected:
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "rows": tuple(row.canonical_dict() for row in self.rows),
            "schema_version": self.schema_version,
        }


def build_token_safety_read_model(
    ledger: EvidenceLedger, *, verify_replay: bool = True
) -> TokenSafetyReadModel:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if not isinstance(verify_replay, bool):
        raise TypeError("verify_replay must be boolean")
    rows: list[TokenSafetyReadRow] = []
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "token_safety_observation":
            continue
        data = payload.data.get("token_safety")
        if not hasattr(data, "get"):
            raise ValueError("invalid token safety payload in Ledger")
        observation = TokenSafetyObservation(
            token=data["token"],
            observed_at=data["observed_at"],
            mint_authority=data["mint"],
            freeze_authority=data["freeze_authority"],
            update_authority=data["update_authority"],
            liquidity_amount=data["liquidity_amount"],
            holder_concentration_bps=data["holder_concentration_bps"],
            deployer=data["deployer"],
            observation_id=data["observation_id"],
            schema_version=data["schema_version"],
        )
        replay_verified = (
            replay_verify_token_safety_observation(observation, ledger).matches
            if verify_replay
            else False
        )
        rows.append(
            TokenSafetyReadRow(
                observation=observation,
                evidence_id=payload.get_canonical_id(),
                replay_verified=replay_verified,
            )
        )
    rows.sort(
        key=lambda row: (
            row.observation.observed_at,
            row.observation.token,
            row.observation.observation_id,
        )
    )
    identity = {
        "rows": tuple(row.canonical_dict() for row in rows),
        "schema_version": "token_safety_read_model.v1",
    }
    return TokenSafetyReadModel(
        rows=tuple(rows),
        model_id=deterministic_id("token_safety_read_model", identity),
    )


__all__ = ["TokenSafetyReadModel", "TokenSafetyReadRow", "build_token_safety_read_model"]
