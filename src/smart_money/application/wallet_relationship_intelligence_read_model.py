from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.wallet_relationship_intelligence import (
    WalletRelationshipIntelligence,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_relationship_intelligence_read_model.v1"


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceReadRow:
    intelligence: WalletRelationshipIntelligence
    ledger_evidence_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.intelligence, WalletRelationshipIntelligence):
            raise TypeError("intelligence must be WalletRelationshipIntelligence")
        if not isinstance(self.ledger_evidence_id, str) or not self.ledger_evidence_id.strip():
            raise ValueError("ledger_evidence_id must be non-empty")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "intelligence": self.intelligence.canonical_dict(),
            "ledger_evidence_id": self.ledger_evidence_id,
        }


@dataclass(frozen=True, slots=True)
class WalletRelationshipIntelligenceReadModel:
    rows: tuple[WalletRelationshipIntelligenceReadRow, ...]
    model_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(item, WalletRelationshipIntelligenceReadRow) for item in self.rows
        ):
            raise TypeError("rows must be tuple of WalletRelationshipIntelligenceReadRow")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet relationship intelligence read model schema_version")
        identity = {
            "rows": tuple(item.canonical_dict() for item in self.rows),
            "schema_version": self.schema_version,
        }
        if self.model_id != deterministic_id("wallet_relationship_intelligence_read_model", identity):
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "rows": tuple(item.canonical_dict() for item in self.rows),
            "schema_version": self.schema_version,
        }


def build_wallet_relationship_intelligence_read_model(
    ledger: EvidenceLedger,
) -> WalletRelationshipIntelligenceReadModel:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    rows: list[WalletRelationshipIntelligenceReadRow] = []
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "wallet_relationship_intelligence":
            continue
        data = payload.data.get("wallet_relationship_intelligence")
        if not hasattr(data, "get"):
            raise ValueError("invalid wallet relationship intelligence payload in Ledger")
        identity = {
            "cluster_id": data["cluster_id"],
            "relationship_count": data["relationship_count"],
            "relationship_ids": tuple(data["relationship_ids"]),
            "schema_version": data["schema_version"],
            "wallets": tuple(data["wallets"]),
        }
        intelligence = WalletRelationshipIntelligence(
            **identity,
            intelligence_id=data["intelligence_id"],
        )
        rows.append(
            WalletRelationshipIntelligenceReadRow(
                intelligence=intelligence,
                ledger_evidence_id=payload.get_canonical_id(),
            )
        )
    rows.sort(key=lambda item: item.intelligence.intelligence_id)
    identity = {
        "rows": tuple(item.canonical_dict() for item in rows),
        "schema_version": _SCHEMA_VERSION,
    }
    return WalletRelationshipIntelligenceReadModel(
        tuple(rows),
        deterministic_id("wallet_relationship_intelligence_read_model", identity),
    )


__all__ = [
    "WalletRelationshipIntelligenceReadModel",
    "WalletRelationshipIntelligenceReadRow",
    "build_wallet_relationship_intelligence_read_model",
]
