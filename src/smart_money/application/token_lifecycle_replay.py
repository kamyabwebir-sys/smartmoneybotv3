from __future__ import annotations

from dataclasses import dataclass

from smart_money.application.token_lifecycle_ledger_projection import TokenLifecycleLedgerProjection
from smart_money.application.token_lifecycle_observation_binding import TokenLifecycleObservationBinding


@dataclass(frozen=True, slots=True)
class TokenLifecycleReplayVerification:
    lifecycle_id: str
    replay_matches: bool
    schema_version: str = "token_lifecycle_replay_verification.v1"


def verify_token_lifecycle_replay(
    binding: TokenLifecycleObservationBinding,
    projection: TokenLifecycleLedgerProjection,
) -> TokenLifecycleReplayVerification:
    rebuilt = TokenLifecycleLedgerProjection.from_binding(binding)
    return TokenLifecycleReplayVerification(
        lifecycle_id=projection.lifecycle_id,
        replay_matches=rebuilt.payload.get_canonical_id() == projection.payload.get_canonical_id(),
    )


__all__ = ["TokenLifecycleReplayVerification", "verify_token_lifecycle_replay"]
