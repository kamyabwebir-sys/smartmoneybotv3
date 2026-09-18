from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.adapters.persistence.wallet_cohort_replay_store import (
    JsonWalletCohortReplayStore,
)
from smart_money.application.wallet_cohort_replay import WalletCohortReplayReceipt
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_cohort_replay_store_verifier.v1"


@dataclass(frozen=True, slots=True)
class WalletCohortReplayStoreVerificationReceipt:
    replay_id: str
    matches: bool
    verification_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("replay_id", "verification_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet cohort replay store verifier schema_version")
        if self.verification_id != deterministic_id(
            "wallet_cohort_replay_store_verification", self.identity_payload()
        ):
            raise ValueError("verification_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "replay_id": self.replay_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"verification_id": self.verification_id, **self.identity_payload()}


def verify_wallet_cohort_replay_store(
    store: JsonWalletCohortReplayStore,
    expected: WalletCohortReplayReceipt,
) -> WalletCohortReplayStoreVerificationReceipt:
    if not isinstance(store, JsonWalletCohortReplayStore):
        raise TypeError("store must be JsonWalletCohortReplayStore")
    if not isinstance(expected, WalletCohortReplayReceipt):
        raise TypeError("expected must be WalletCohortReplayReceipt")
    retained = store.get(expected.replay_id)
    if retained is None:
        raise ValueError("expected wallet cohort replay receipt is missing from Store")
    if retained.canonical_dict() != expected.canonical_dict():
        raise ValueError("stored wallet cohort replay receipt does not match expected receipt")
    return WalletCohortReplayStoreVerificationReceipt(
        replay_id=expected.replay_id,
        matches=True,
        verification_id=deterministic_id(
            "wallet_cohort_replay_store_verification",
            {
                "matches": True,
                "replay_id": expected.replay_id,
                "schema_version": _SCHEMA_VERSION,
            },
        ),
    )


__all__ = [
    "WalletCohortReplayStoreVerificationReceipt",
    "verify_wallet_cohort_replay_store",
]
