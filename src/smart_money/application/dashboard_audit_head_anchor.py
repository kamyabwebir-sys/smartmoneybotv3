from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_query_audit_chain import (
    DashboardQueryAuditChain,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardAuditHeadAnchor:
    """Trusted immutable anchor for the current dashboard audit chain head."""

    chain_id: str
    chain_hash: str
    receipt_count: int
    latest_verification_id: str | None
    schema_version: str = "dashboard_audit_head_anchor.v1"

    def __post_init__(self) -> None:
        for name in ("chain_id", "chain_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(self.chain_hash) != 64:
            raise ValueError("chain_hash must be a SHA-256 hex digest")
        if not isinstance(self.receipt_count, int) or isinstance(
            self.receipt_count, bool
        ) or self.receipt_count < 0:
            raise ValueError("receipt_count must be a non-negative integer")
        if self.latest_verification_id is not None and not isinstance(
            self.latest_verification_id, str
        ):
            raise TypeError("latest_verification_id must be a string or None")
        if self.schema_version != "dashboard_audit_head_anchor.v1":
            raise ValueError("unsupported dashboard head anchor schema_version")

    @classmethod
    def from_chain(
        cls,
        chain: DashboardQueryAuditChain,
    ) -> DashboardAuditHeadAnchor:
        if not isinstance(chain, DashboardQueryAuditChain):
            raise TypeError("chain must be a DashboardQueryAuditChain")
        return cls(
            chain_id=chain.chain_id,
            chain_hash=chain.chain_hash,
            receipt_count=len(chain.receipts),
            latest_verification_id=(
                None
                if not chain.receipts
                else chain.receipts[-1].verification_id
            ),
        )

    def matches(self, chain: DashboardQueryAuditChain) -> bool:
        return self == DashboardAuditHeadAnchor.from_chain(chain)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_hash": self.chain_hash,
            "chain_id": self.chain_id,
            "latest_verification_id": self.latest_verification_id,
            "receipt_count": self.receipt_count,
            "schema_version": self.schema_version,
        }

    @property
    def anchor_id(self) -> str:
        return deterministic_id("dashboard_audit_head_anchor", self.canonical_dict())


__all__ = ["DashboardAuditHeadAnchor"]
