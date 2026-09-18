from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_session_final_audit_chain import (
    DashboardSessionFinalAuditChain,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalAuditChainReplayReceipt:
    expected_chain_id: str
    actual_chain_id: str
    expected_chain_hash: str
    actual_chain_hash: str
    expected_entry_count: int
    actual_entry_count: int
    matches: bool
    mismatches: tuple[str, ...] = ()
    schema_version: str = "dashboard_session_final_audit_chain_replay.v1"

    def __post_init__(self) -> None:
        for name in (
            "expected_chain_id",
            "actual_chain_id",
            "expected_chain_hash",
            "actual_chain_hash",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        for name in ("expected_chain_hash", "actual_chain_hash"):
            if len(getattr(self, name)) != 64:
                raise ValueError(f"{name} must be a SHA-256 hex digest")
        for name in ("expected_entry_count", "actual_entry_count"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be non-negative")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be a boolean")
        if not isinstance(self.mismatches, tuple) or not all(
            isinstance(item, str) and item.strip()
            for item in self.mismatches
        ):
            raise TypeError("mismatches must be a tuple of text values")
        if self.matches and self.mismatches:
            raise ValueError("matching replay cannot contain mismatches")
        if not self.matches and not self.mismatches:
            raise ValueError("non-matching replay requires mismatches")
        if (
            self.schema_version
            != "dashboard_session_final_audit_chain_replay.v1"
        ):
            raise ValueError(
                "unsupported final audit chain replay schema_version"
            )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "actual_chain_hash": self.actual_chain_hash,
            "actual_chain_id": self.actual_chain_id,
            "actual_entry_count": self.actual_entry_count,
            "expected_chain_hash": self.expected_chain_hash,
            "expected_chain_id": self.expected_chain_id,
            "expected_entry_count": self.expected_entry_count,
            "matches": self.matches,
            "mismatches": list(self.mismatches),
            "schema_version": self.schema_version,
        }

    @property
    def verification_id(self) -> str:
        return deterministic_id(
            "dashboard_session_final_audit_chain_replay",
            self.canonical_dict(),
        )


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalAuditChainReplayVerifier:
    def verify(
        self,
        expected: DashboardSessionFinalAuditChain,
        actual: DashboardSessionFinalAuditChain,
    ) -> DashboardSessionFinalAuditChainReplayReceipt:
        if not isinstance(expected, DashboardSessionFinalAuditChain):
            raise TypeError(
                "expected must be a DashboardSessionFinalAuditChain"
            )
        if not isinstance(actual, DashboardSessionFinalAuditChain):
            raise TypeError("actual must be a DashboardSessionFinalAuditChain")
        mismatches = tuple(
            field
            for field in ("chain_id", "chain_hash", "entry_count")
            if (
                getattr(expected, field)
                if field != "entry_count"
                else len(expected.entries)
            )
            != (
                getattr(actual, field)
                if field != "entry_count"
                else len(actual.entries)
            )
        )
        return DashboardSessionFinalAuditChainReplayReceipt(
            expected_chain_id=expected.chain_id,
            actual_chain_id=actual.chain_id,
            expected_chain_hash=expected.chain_hash,
            actual_chain_hash=actual.chain_hash,
            expected_entry_count=len(expected.entries),
            actual_entry_count=len(actual.entries),
            matches=not mismatches,
            mismatches=mismatches,
        )


__all__ = [
    "DashboardSessionFinalAuditChainReplayReceipt",
    "DashboardSessionFinalAuditChainReplayVerifier",
]
