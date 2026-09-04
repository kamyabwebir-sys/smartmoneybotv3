from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSessionAuditHeadAnchor:
    """Trusted immutable anchor for the session audit chain head."""

    chain_id: str
    chain_hash: str
    entry_count: int
    latest_entry_id: str | None
    latest_entry_kind: str | None
    schema_version: str = "dashboard_session_audit_head_anchor.v1"

    def __post_init__(self) -> None:
        for name in ("chain_id", "chain_hash"):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ).strip():
                raise ValueError(f"{name} must be non-empty")
        if len(self.chain_hash) != 64:
            raise ValueError("chain_hash must be a SHA-256 hex digest")
        if not isinstance(self.entry_count, int) or isinstance(
            self.entry_count, bool
        ) or self.entry_count < 0:
            raise ValueError("entry_count must be non-negative")
        for name in ("latest_entry_id", "latest_entry_kind"):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"{name} must be non-empty or None")
        if self.entry_count == 0 and (
            self.latest_entry_id is not None or self.latest_entry_kind is not None
        ):
            raise ValueError("empty chain cannot have a latest entry")
        if self.schema_version != "dashboard_session_audit_head_anchor.v1":
            raise ValueError("unsupported session head anchor schema_version")

    @classmethod
    def from_chain(
        cls,
        chain: DashboardSessionAuditChain,
    ) -> DashboardSessionAuditHeadAnchor:
        if not isinstance(chain, DashboardSessionAuditChain):
            raise TypeError("chain must be a DashboardSessionAuditChain")
        latest = chain.entries[-1] if chain.entries else None
        return cls(
            chain_id=chain.chain_id,
            chain_hash=chain.chain_hash,
            entry_count=len(chain.entries),
            latest_entry_id=None if latest is None else latest.entry_id,
            latest_entry_kind=None if latest is None else latest.entry_kind,
        )

    def matches(self, chain: DashboardSessionAuditChain) -> bool:
        return self == DashboardSessionAuditHeadAnchor.from_chain(chain)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_hash": self.chain_hash,
            "chain_id": self.chain_id,
            "entry_count": self.entry_count,
            "latest_entry_id": self.latest_entry_id,
            "latest_entry_kind": self.latest_entry_kind,
            "schema_version": self.schema_version,
        }

    @property
    def anchor_id(self) -> str:
        return deterministic_id(
            "dashboard_session_audit_head_anchor",
            self.canonical_dict(),
        )


__all__ = ["DashboardSessionAuditHeadAnchor"]
