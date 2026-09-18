from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_query_replay_verifier import (
    DashboardQueryReplayReceipt,
)
from smart_money.core.serialization import canonical_json


@dataclass(frozen=True, slots=True)
class DashboardQueryAuditChain:
    """Canonical hash chain for ordered dashboard replay receipts."""

    receipts: tuple[DashboardQueryReplayReceipt, ...]
    chain_hash: str
    schema_version: str = "dashboard_query_audit_chain.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.receipts, tuple) or not all(
            isinstance(item, DashboardQueryReplayReceipt)
            for item in self.receipts
        ):
            raise TypeError("receipts must be a tuple of replay receipts")
        if not isinstance(self.chain_hash, str) or len(self.chain_hash) != 64:
            raise ValueError("chain_hash must be a SHA-256 hex digest")
        expected = _chain_hash(self.receipts)
        if self.chain_hash != expected:
            raise ValueError("audit chain hash mismatch")
        if self.schema_version != "dashboard_query_audit_chain.v1":
            raise ValueError("unsupported dashboard audit chain schema_version")

    @classmethod
    def from_receipts(
        cls,
        receipts: tuple[DashboardQueryReplayReceipt, ...]
        | list[DashboardQueryReplayReceipt],
    ) -> DashboardQueryAuditChain:
        normalized = tuple(receipts)
        return cls(receipts=normalized, chain_hash=_chain_hash(normalized))

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_hash": self.chain_hash,
            "receipts": [item.canonical_dict() for item in self.receipts],
            "schema_version": self.schema_version,
        }

    @property
    def chain_id(self) -> str:
        return hashlib.sha256(
            canonical_json(self.canonical_dict()).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class DashboardQueryAuditChainVerifier:
    """Fail-closed verification of receipt continuity and ordering."""

    def verify(
        self,
        chain: DashboardQueryAuditChain,
        receipts: tuple[DashboardQueryReplayReceipt, ...]
        | list[DashboardQueryReplayReceipt],
    ) -> bool:
        if not isinstance(chain, DashboardQueryAuditChain):
            raise TypeError("chain must be a DashboardQueryAuditChain")
        candidate = tuple(receipts)
        if not all(
            isinstance(item, DashboardQueryReplayReceipt) for item in candidate
        ):
            raise TypeError("receipts must contain replay receipts")
        if len({item.verification_id for item in candidate}) != len(candidate):
            raise ValueError("audit chain contains duplicate verification IDs")
        return candidate == chain.receipts and _chain_hash(candidate) == chain.chain_hash


def _chain_hash(receipts: tuple[DashboardQueryReplayReceipt, ...]) -> str:
    previous = "0" * 64
    for receipt in receipts:
        previous = hashlib.sha256(
            canonical_json(
                {
                    "previous_hash": previous,
                    "receipt": receipt.canonical_dict(),
                }
            ).encode("utf-8")
        ).hexdigest()
    return previous


__all__ = ["DashboardQueryAuditChain", "DashboardQueryAuditChainVerifier"]
