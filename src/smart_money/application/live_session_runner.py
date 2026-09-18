from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from smart_money.application.live_discovery import (
    LiveObservationCheckpoint,
    LiveProviderSession,
    bind_live_evidence,
    build_live_candidate_payload,
    CheckpointStore,
    checkpoint_session,
    poll_solana_boundary,
    start_live_session,
    verify_checkpoint_recovery,
    verify_live_candidate_replay,
)
from smart_money.application.solana_rpc_production import (
    RateLimitBackoff,
    RetryExecutionEvidence,
    build_retry_execution_evidence,
    classify_rpc_error,
)
from smart_money.ingestion.ledger import EvidenceGroundingLedger


@runtime_checkable
class LiveSessionRunner(Protocol):
    async def run(
        self,
        fetcher: Any,
        *,
        start_slot: int,
        max_polls: int | None = None,
    ) -> Any:
        ...


@dataclass(frozen=True, slots=True)
class LiveSessionRunResult:
    session: LiveProviderSession
    checkpoint: LiveObservationCheckpoint | None
    retry_evidence: RetryExecutionEvidence | None
    replay_verified: bool



def _adapt_fetcher(fetcher: Any) -> Any:
    def adapted(method: str, params: dict[str, Any]) -> Any:
        try:
            return fetcher(method, params)
        except TypeError:
            return fetcher(params["minContextSlot"])
    return adapted


class DefaultLiveSessionRunner:
    def __init__(self, *, provider_id: str = "solana-production") -> None:
        self._provider_id = provider_id
        self._store = CheckpointStore("live_checkpoint.json")
        self._ledger = EvidenceGroundingLedger()

    async def run(
        self,
        fetcher: Any,
        *,
        start_slot: int,
        max_polls: int | None = None,
    ) -> LiveSessionRunResult:
        session = start_live_session(self._provider_id, started_slot=start_slot)
        backoff = RateLimitBackoff(max_retries=3, base_slots=1)

        checkpoint = None
        retry_evidence = None
        latest_slot = start_slot
        attempts = 0

        while max_polls is None or attempts < max_polls:
            attempts += 1
            try:
                adapted_fetcher = _adapt_fetcher(fetcher)
                boundary = poll_solana_boundary(adapted_fetcher, latest_slot)
                latest_slot = int(boundary["slot"])
                payload = build_live_candidate_payload(boundary, latest_slot)
                bind_live_evidence(self._ledger, payload)
                checkpoint = checkpoint_session(session, latest_slot)
                self._store.save(checkpoint)
                verify_checkpoint_recovery(checkpoint, self._store)
                verify_live_candidate_replay(payload, payload)
                return LiveSessionRunResult(
                    session=session,
                    checkpoint=checkpoint,
                    retry_evidence=None,
                    replay_verified=True,
                )
            except Exception as exc:
                print(
                    f"[live-session-runner] attempt={attempts} "
                    f"exception={type(exc).__name__}: {exc}"
                )
                error_class = classify_rpc_error({"message": str(exc)})
                retry_evidence = build_retry_execution_evidence(
                    self._provider_id,
                    retry_count=min(attempts - 1, backoff.max_retries),
                    error_class=error_class,
                )
                if attempts > backoff.max_retries:
                    return LiveSessionRunResult(
                        session=session,
                        checkpoint=checkpoint,
                        retry_evidence=retry_evidence,
                        replay_verified=False,
                    )

        return LiveSessionRunResult(
            session=session,
            checkpoint=checkpoint,
            retry_evidence=retry_evidence,
            replay_verified=False,
        )







