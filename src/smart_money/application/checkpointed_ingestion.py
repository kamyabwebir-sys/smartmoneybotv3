from __future__ import annotations

from dataclasses import dataclass

from smart_money.application.ports.market_state_checkpoint_store import (
    MarketStateCheckpointStore,
)
from smart_money.application.ports.market_state_ingestion import (
    CheckpointableMarketProvider,
    IdempotentMarketStateConsumer,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.market_identity import MarketId
from smart_money.domain.market_state import MarketStateCheckpoint


@dataclass(frozen=True, slots=True)
class CheckpointedIngestionResult:
    """Deterministic receipt for one bounded or source-complete session."""

    session_id: str
    provider_id: str
    market_id: str
    resumed_from_checkpoint_id: str | None
    first_accepted_event_id: str | None
    last_accepted_event_id: str | None
    accepted_count: int
    final_checkpoint_id: str | None
    schema_version: str = "checkpointed_ingestion_result.v1"

    def __post_init__(self) -> None:
        for field_name in ("session_id", "provider_id", "market_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if isinstance(self.accepted_count, bool) or not isinstance(
            self.accepted_count,
            int,
        ):
            raise TypeError("accepted_count must be an integer")
        if self.accepted_count < 0:
            raise ValueError("accepted_count must be non-negative")
        if self.schema_version != "checkpointed_ingestion_result.v1":
            raise ValueError("unsupported ingestion result schema_version")
        for field_name in (
            "resumed_from_checkpoint_id",
            "first_accepted_event_id",
            "last_accepted_event_id",
            "final_checkpoint_id",
        ):
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"{field_name} must be None or non-empty")
        event_ids = (
            self.first_accepted_event_id,
            self.last_accepted_event_id,
        )
        if self.accepted_count == 0:
            if any(value is not None for value in event_ids):
                raise ValueError("empty session must not contain accepted event IDs")
        elif any(
            not isinstance(value, str) or not value.strip()
            for value in event_ids
        ):
            raise ValueError("non-empty session requires accepted event IDs")
        elif self.final_checkpoint_id is None:
            raise ValueError("non-empty session requires final_checkpoint_id")
        expected_id = deterministic_id(
            "checkpointed_ingestion_result",
            self.identity_payload(),
        )
        if self.session_id != expected_id:
            raise ValueError("session_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, object]:
        return {
            "accepted_count": self.accepted_count,
            "final_checkpoint_id": self.final_checkpoint_id,
            "first_accepted_event_id": self.first_accepted_event_id,
            "last_accepted_event_id": self.last_accepted_event_id,
            "market_id": self.market_id,
            "provider_id": self.provider_id,
            "resumed_from_checkpoint_id": self.resumed_from_checkpoint_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"session_id": self.session_id, **self.identity_payload()}


@dataclass(frozen=True, slots=True)
class CheckpointedIngestionSession:
    """Deliver canonical events with at-least-once, checkpoint-after-ack semantics."""

    provider: CheckpointableMarketProvider
    consumer: IdempotentMarketStateConsumer
    checkpoint_store: MarketStateCheckpointStore

    def __post_init__(self) -> None:
        if not isinstance(self.provider, CheckpointableMarketProvider):
            raise TypeError("provider must satisfy CheckpointableMarketProvider")
        if not isinstance(self.consumer, IdempotentMarketStateConsumer):
            raise TypeError("consumer must satisfy IdempotentMarketStateConsumer")
        if not isinstance(self.checkpoint_store, MarketStateCheckpointStore):
            raise TypeError("checkpoint_store must satisfy its application port")

    async def run(
        self,
        market: MarketId,
        *,
        max_events: int | None = None,
    ) -> CheckpointedIngestionResult:
        if not isinstance(market, MarketId):
            raise TypeError("market must be a MarketId")
        self._validate_max_events(max_events)
        checkpoint = self._load_checkpoint()
        if checkpoint is None:
            stream = self.provider.stream_state_changes(market)
        else:
            if checkpoint.market.canonical_id != market.canonical_id:
                raise ValueError("stored checkpoint market does not match session")
            stream = self.provider.stream_from_checkpoint(checkpoint)

        accepted_count = 0
        first_event_id: str | None = None
        last_event_id: str | None = None
        final_checkpoint = checkpoint
        async for change in stream:
            acknowledged_id = await self.consumer.accept(change)
            if acknowledged_id != change.event_id:
                raise ValueError("consumer acknowledgement does not match event_id")
            next_checkpoint = self.provider.checkpoint_for(change)
            self.checkpoint_store.save(next_checkpoint)
            if first_event_id is None:
                first_event_id = change.event_id
            last_event_id = change.event_id
            accepted_count += 1
            final_checkpoint = next_checkpoint
            if max_events is not None and accepted_count >= max_events:
                break

        return self._result(
            market=market,
            initial_checkpoint=checkpoint,
            final_checkpoint=final_checkpoint,
            first_event_id=first_event_id,
            last_event_id=last_event_id,
            accepted_count=accepted_count,
        )

    def _load_checkpoint(self) -> MarketStateCheckpoint | None:
        try:
            return self.checkpoint_store.load()
        except FileNotFoundError:
            return None

    def _result(
        self,
        *,
        market: MarketId,
        initial_checkpoint: MarketStateCheckpoint | None,
        final_checkpoint: MarketStateCheckpoint | None,
        first_event_id: str | None,
        last_event_id: str | None,
        accepted_count: int,
    ) -> CheckpointedIngestionResult:
        payload = {
            "accepted_count": accepted_count,
            "final_checkpoint_id": (
                None
                if final_checkpoint is None
                else final_checkpoint.checkpoint_id
            ),
            "first_accepted_event_id": first_event_id,
            "last_accepted_event_id": last_event_id,
            "market_id": market.canonical_id,
            "provider_id": self.provider.provider_id,
            "resumed_from_checkpoint_id": (
                None
                if initial_checkpoint is None
                else initial_checkpoint.checkpoint_id
            ),
            "schema_version": "checkpointed_ingestion_result.v1",
        }
        return CheckpointedIngestionResult(
            session_id=deterministic_id(
                "checkpointed_ingestion_result",
                payload,
            ),
            provider_id=self.provider.provider_id,
            market_id=market.canonical_id,
            resumed_from_checkpoint_id=payload[
                "resumed_from_checkpoint_id"
            ],
            first_accepted_event_id=first_event_id,
            last_accepted_event_id=last_event_id,
            accepted_count=accepted_count,
            final_checkpoint_id=payload["final_checkpoint_id"],
        )

    @staticmethod
    def _validate_max_events(max_events: int | None) -> None:
        if max_events is None:
            return
        if isinstance(max_events, bool) or not isinstance(max_events, int):
            raise TypeError("max_events must be an integer or None")
        if max_events <= 0:
            raise ValueError("max_events must be positive")


__all__ = [
    "CheckpointedIngestionResult",
    "CheckpointedIngestionSession",
]
