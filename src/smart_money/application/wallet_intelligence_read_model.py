from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.wallet_intelligence_replay import (
    replay_verify_wallet_intelligence_observation,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.wallet_intelligence import WalletIntelligenceObservation

_SCHEMA_VERSION = "wallet_intelligence_read_model.v1"


@dataclass(frozen=True, slots=True)
class WalletIntelligenceReadRow:
    observation: WalletIntelligenceObservation
    evidence_id: str
    replay_verified: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "observation": self.observation.canonical_dict(),
            "replay_verified": self.replay_verified,
        }


@dataclass(frozen=True, slots=True)
class WalletIntelligenceReadModel:
    rows: tuple[WalletIntelligenceReadRow, ...]
    model_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple):
            raise TypeError("rows must be a tuple")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet intelligence read model schema_version")
        expected = deterministic_id(
            "wallet_intelligence_read_model",
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


def build_wallet_intelligence_read_model(
    ledger: EvidenceLedger, *, verify_replay: bool = True
) -> WalletIntelligenceReadModel:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if not isinstance(verify_replay, bool):
        raise TypeError("verify_replay must be boolean")
    rows: list[WalletIntelligenceReadRow] = []
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "wallet_intelligence_observation":
            continue
        data = payload.data.get("wallet_intelligence")
        if not hasattr(data, "get"):
            raise ValueError("invalid wallet intelligence payload in Ledger")
        observation = WalletIntelligenceObservation(
            wallet=data["wallet"],
            observed_from_slot=data["observed_from_slot"],
            observed_to_slot=data["observed_to_slot"],
            activity_count=data["activity_count"],
            buy_count=data["buy_count"],
            sell_count=data["sell_count"],
            unknown_count=data["unknown_count"],
            distinct_token_count=data["distinct_token_count"],
            token_delta_total=data["token_delta_total"],
            native_delta_total=data["native_delta_total"],
            data_completeness_bps=data["data_completeness_bps"],
            observation_id=data["observation_id"],
            schema_version=data["schema_version"],
        )
        replay_verified = (
            replay_verify_wallet_intelligence_observation(observation, ledger).matches
            if verify_replay
            else False
        )
        rows.append(
            WalletIntelligenceReadRow(
                observation=observation,
                evidence_id=payload.get_canonical_id(),
                replay_verified=replay_verified,
            )
        )
    rows.sort(
        key=lambda row: (
            row.observation.wallet,
            row.observation.observed_from_slot,
            row.observation.observation_id,
        )
    )
    identity = {
        "rows": tuple(row.canonical_dict() for row in rows),
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletIntelligenceReadModel(
        rows=tuple(rows),
        model_id=deterministic_id("wallet_intelligence_read_model", identity),
    )


__all__ = [
    "WalletIntelligenceReadModel",
    "WalletIntelligenceReadRow",
    "build_wallet_intelligence_read_model",
]
