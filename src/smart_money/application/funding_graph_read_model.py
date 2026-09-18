from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_graph_evidence import FundingGraphEvidence
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "funding_graph_read_model.v1"


@dataclass(frozen=True, slots=True)
class FundingGraphReadRow:
    evidence: FundingGraphEvidence
    ledger_evidence_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, FundingGraphEvidence):
            raise TypeError("evidence must be FundingGraphEvidence")
        if not isinstance(self.ledger_evidence_id, str) or not self.ledger_evidence_id.strip():
            raise ValueError("ledger_evidence_id must be non-empty")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "evidence": self.evidence.canonical_dict(),
            "ledger_evidence_id": self.ledger_evidence_id,
        }


@dataclass(frozen=True, slots=True)
class FundingGraphReadModel:
    rows: tuple[FundingGraphReadRow, ...]
    model_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(item, FundingGraphReadRow) for item in self.rows
        ):
            raise TypeError("rows must be a tuple of FundingGraphReadRow")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported funding graph read model schema_version")
        expected = deterministic_id(
            "funding_graph_read_model",
            {"rows": tuple(item.canonical_dict() for item in self.rows), "schema_version": self.schema_version},
        )
        if self.model_id != expected:
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "rows": tuple(item.canonical_dict() for item in self.rows),
            "schema_version": self.schema_version,
        }


def build_funding_graph_read_model(ledger: EvidenceLedger) -> FundingGraphReadModel:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    rows: list[FundingGraphReadRow] = []
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "funding_graph_evidence":
            continue
        data = payload.data.get("funding_graph")
        if not hasattr(data, "get"):
            raise ValueError("invalid funding graph payload in Ledger")
        identity = {
            "chain": data["chain"],
            "native_amount": data["native_amount"],
            "observed_slot": data["observed_slot"],
            "provenance": dict(data["provenance"]),
            "schema_version": data["schema_version"],
            "source_wallet": data["source_wallet"],
            "target_wallet": data["target_wallet"],
            "transaction_signature": data["transaction_signature"],
        }
        evidence = FundingGraphEvidence(
            **identity,
            evidence_id=data["evidence_id"],
        )
        rows.append(FundingGraphReadRow(evidence=evidence, ledger_evidence_id=payload.get_canonical_id()))
    rows.sort(key=lambda item: (item.evidence.observed_slot, item.evidence.source_wallet, item.evidence.target_wallet, item.evidence.evidence_id))
    identity = {"rows": tuple(item.canonical_dict() for item in rows), "schema_version": _SCHEMA_VERSION}
    return FundingGraphReadModel(tuple(rows), deterministic_id("funding_graph_read_model", identity))


__all__ = ["FundingGraphReadModel", "FundingGraphReadRow", "build_funding_graph_read_model"]
