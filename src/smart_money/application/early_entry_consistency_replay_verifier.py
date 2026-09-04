from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.early_entry_consistency import EarlyEntryConsistency
from smart_money.application.early_entry_consistency_compatibility import (
    replay_early_entry_consistency_compatibility,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "early_entry_consistency_replay_verifier.v1"


@dataclass(frozen=True, slots=True)
class EarlyEntryConsistencyReplayReceipt:
    consistency_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("consistency_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported replay verifier schema_version")
        if self.replay_id != deterministic_id(
            "early_entry_consistency_replay_verifier", self.identity_payload()
        ):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "consistency_id": self.consistency_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def verify_early_entry_consistency_replay(
    expected: EarlyEntryConsistency,
    ledger: EvidenceLedger,
) -> EarlyEntryConsistencyReplayReceipt:
    if not isinstance(expected, EarlyEntryConsistency):
        raise TypeError("expected must be EarlyEntryConsistency")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    replayed = replay_early_entry_consistency_compatibility(ledger)
    matches = any(item.canonical_dict() == expected.canonical_dict() for item in replayed)
    if not matches:
        raise ValueError("early entry consistency replay does not match expected value")
    return EarlyEntryConsistencyReplayReceipt(
        consistency_id=expected.consistency_id,
        matches=True,
        replay_id=deterministic_id(
            "early_entry_consistency_replay_verifier",
            {
                "consistency_id": expected.consistency_id,
                "matches": True,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


def verify_all_early_entry_consistency_replays(
    ledger: EvidenceLedger,
) -> tuple[EarlyEntryConsistencyReplayReceipt, ...]:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    return tuple(
        EarlyEntryConsistencyReplayReceipt(
            consistency_id=item.consistency_id,
            matches=True,
            replay_id=deterministic_id(
                "early_entry_consistency_replay_verifier",
                {
                    "consistency_id": item.consistency_id,
                    "matches": True,
                    "schema_version": _SCHEMA_VERSION,
                },
            ),
        )
        for item in replay_early_entry_consistency_compatibility(ledger)
    )


__all__ = [
    "EarlyEntryConsistencyReplayReceipt",
    "verify_early_entry_consistency_replay",
    "verify_all_early_entry_consistency_replays",
]
