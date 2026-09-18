from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_behavior_fingerprint import WalletBehaviorFingerprint
from smart_money.application.wallet_cohort_detection import WalletCohort, detect_wallet_cohorts
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_cohort_replay.v1"


@dataclass(frozen=True, slots=True)
class WalletCohortReplayReceipt:
    cohort_id: str
    matches: bool
    replay_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("cohort_id", "replay_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet cohort replay schema_version")
        if self.replay_id != deterministic_id("wallet_cohort_replay", self.identity_payload()):
            raise ValueError("replay_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "cohort_id": self.cohort_id,
            "matches": self.matches,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"replay_id": self.replay_id, **self.identity_payload()}


def replay_verify_wallet_cohort(
    expected: WalletCohort,
    fingerprints: tuple[WalletBehaviorFingerprint, ...],
    *,
    bucket_size_bps: int = 1000,
) -> WalletCohortReplayReceipt:
    if not isinstance(expected, WalletCohort):
        raise TypeError("expected must be WalletCohort")
    if not isinstance(fingerprints, tuple) or not all(
        isinstance(item, WalletBehaviorFingerprint) for item in fingerprints
    ):
        raise TypeError("fingerprints must be a tuple of WalletBehaviorFingerprint")
    rebuilt = next(
        (item for item in detect_wallet_cohorts(fingerprints, bucket_size_bps=bucket_size_bps)
         if item.cohort_id == expected.cohort_id),
        None,
    )
    if rebuilt is None or rebuilt.canonical_dict() != expected.canonical_dict():
        raise ValueError("wallet cohort replay does not match expected cohort")
    return WalletCohortReplayReceipt(
        cohort_id=expected.cohort_id,
        matches=True,
        replay_id=deterministic_id(
            "wallet_cohort_replay",
            {
                "cohort_id": expected.cohort_id,
                "matches": True,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = ["WalletCohortReplayReceipt", "replay_verify_wallet_cohort"]
