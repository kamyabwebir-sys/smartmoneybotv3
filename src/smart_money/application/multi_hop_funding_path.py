from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.funding_graph_read_model import (
    FundingGraphReadModel,
    FundingGraphReadRow,
)
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "multi_hop_funding_path.v1"


@dataclass(frozen=True, slots=True)
class MultiHopFundingPath:
    wallets: tuple[str, ...]
    edge_evidence_ids: tuple[str, ...]
    total_native_amount: int
    path_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.wallets, tuple) or len(self.wallets) < 3:
            raise ValueError("wallets must contain at least three nodes")
        if len(self.edge_evidence_ids) != len(self.wallets) - 1:
            raise ValueError("edge count must be hops")
        if len(set(self.wallets)) != len(self.wallets):
            raise ValueError("funding path cannot contain cycles")
        if not all(isinstance(item, str) and item.strip() for item in self.wallets + self.edge_evidence_ids):
            raise ValueError("path identifiers must be non-empty strings")
        if isinstance(self.total_native_amount, bool) or not isinstance(self.total_native_amount, int) or self.total_native_amount < 0:
            raise ValueError("total_native_amount must be non-negative integer")
        if not isinstance(self.path_id, str) or not self.path_id.strip():
            raise ValueError("path_id must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported multi-hop funding path schema_version")
        if self.path_id != deterministic_id("multi_hop_funding_path", self.identity_payload()):
            raise ValueError("path_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "edge_evidence_ids": self.edge_evidence_ids,
            "schema_version": self.schema_version,
            "total_native_amount": self.total_native_amount,
            "wallets": self.wallets,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"path_id": self.path_id, **self.identity_payload()}


def detect_multi_hop_funding_paths(
    model: FundingGraphReadModel,
    *,
    source_wallet: str | None = None,
    target_wallet: str | None = None,
    max_hops: int = 3,
) -> tuple[MultiHopFundingPath, ...]:
    if not isinstance(model, FundingGraphReadModel):
        raise TypeError("model must be FundingGraphReadModel")
    for name, value in (("source_wallet", source_wallet), ("target_wallet", target_wallet)):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{name} must be non-empty")
    if isinstance(max_hops, bool) or not isinstance(max_hops, int) or not 2 <= max_hops <= 8:
        raise ValueError("max_hops must be between 2 and 8")
    edges = sorted(
        model.rows,
        key=lambda row: (
            row.evidence.source_wallet,
            row.evidence.target_wallet,
            row.evidence.observed_slot,
            row.ledger_evidence_id,
        ),
    )
    adjacency: dict[str, list[FundingGraphReadRow]] = {}
    for edge in edges:
        adjacency.setdefault(edge.evidence.source_wallet, []).append(edge)
    found: dict[str, MultiHopFundingPath] = {}

    def visit(wallets: tuple[str, ...], edge_ids: tuple[str, ...], amount: int) -> None:
        current = wallets[-1]
        if len(edge_ids) >= 2 and (target_wallet is None or current == target_wallet.strip()):
            identity = {
                "edge_evidence_ids": edge_ids,
                "schema_version": _SCHEMA_VERSION,
                "total_native_amount": amount,
                "wallets": wallets,
            }
            path = MultiHopFundingPath(
                wallets=wallets,
                edge_evidence_ids=edge_ids,
                total_native_amount=amount,
                path_id=deterministic_id("multi_hop_funding_path", identity),
            )
            found[path.path_id] = path
        if len(edge_ids) >= max_hops:
            return
        for edge in adjacency.get(current, ()):
            target = edge.evidence.target_wallet
            if target in wallets:
                continue
            if target_wallet is not None and target_wallet.strip() not in wallets and len(edge_ids) + 1 >= 2:
                pass
            visit(wallets + (target,), edge_ids + (edge.ledger_evidence_id,), amount + edge.evidence.native_amount)

    starts = [source_wallet.strip()] if source_wallet is not None else sorted(adjacency)
    for start in starts:
        if start in adjacency:
            visit((start,), (), 0)
    return tuple(sorted(found.values(), key=lambda item: item.path_id))


__all__ = ["MultiHopFundingPath", "detect_multi_hop_funding_paths"]
