from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application._validation import (
    require_sha256 as _require_sha256,
)
from smart_money.application._validation import (
    require_text as _require_text,
)
from smart_money.application.checkpointed_ingestion import (
    CheckpointedIngestionResult,
)
from smart_money.application.market_state_observation_consumer import (
    make_canonical_market_state_observation,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.ports.market_state_checkpoint_store import (
    MarketStateCheckpointStore,
)
from smart_money.core.ids import deterministic_id
from smart_money.core.serialization import canonicalize
from smart_money.domain.market_state import MarketStateChange

_SCHEMA_VERSION = "durable_ingestion_commit.v1"


@runtime_checkable
class ContentHashedEvidenceLedger(EvidenceLedger, Protocol):
    @property
    def content_hash(self) -> str:
        """Return the hash of the current canonical Ledger document."""
        ...


@dataclass(frozen=True, slots=True)
class DurableIngestionCommitReceipt:
    """Content-addressed proof joining one session, Evidence, and checkpoint."""

    receipt_id: str
    session_id: str
    provider_id: str
    market_id: str
    event_id: str
    source_event_id: str
    evidence_id: str
    ledger_content_hash: str
    checkpoint_id: str
    accepted_count: int
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "receipt_id",
            "session_id",
            "provider_id",
            "market_id",
            "event_id",
            "source_event_id",
            "evidence_id",
            "checkpoint_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_text(getattr(self, field_name), field_name),
            )
        object.__setattr__(
            self,
            "ledger_content_hash",
            _require_sha256(
                self.ledger_content_hash,
                "ledger_content_hash",
            ),
        )
        if isinstance(self.accepted_count, bool) or not isinstance(
            self.accepted_count,
            int,
        ):
            raise TypeError("accepted_count must be an integer")
        if self.accepted_count <= 0:
            raise ValueError("accepted_count must be positive")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported durable ingestion commit schema_version")
        expected_id = deterministic_id(
            "durable_ingestion_commit",
            self.identity_payload(),
        )
        if self.receipt_id != expected_id:
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, str | int]:
        return {
            "accepted_count": self.accepted_count,
            "checkpoint_id": self.checkpoint_id,
            "event_id": self.event_id,
            "evidence_id": self.evidence_id,
            "ledger_content_hash": self.ledger_content_hash,
            "market_id": self.market_id,
            "provider_id": self.provider_id,
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "source_event_id": self.source_event_id,
        }

    def canonical_dict(self) -> dict[str, str | int]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def create_durable_ingestion_commit_receipt(
    *,
    result: CheckpointedIngestionResult,
    change: MarketStateChange,
    ledger: ContentHashedEvidenceLedger,
    checkpoint_store: MarketStateCheckpointStore,
) -> DurableIngestionCommitReceipt:
    """Create a receipt only after durable Evidence and checkpoint agree."""
    if not isinstance(result, CheckpointedIngestionResult):
        raise TypeError("result must be a CheckpointedIngestionResult")
    if not isinstance(change, MarketStateChange):
        raise TypeError("change must be a MarketStateChange")
    if not isinstance(ledger, ContentHashedEvidenceLedger):
        raise TypeError("ledger must provide EvidenceLedger and content_hash")
    if not isinstance(checkpoint_store, MarketStateCheckpointStore):
        raise TypeError("checkpoint_store must satisfy its application port")
    if result.accepted_count <= 0:
        raise ValueError("result must contain at least one accepted event")
    if result.last_accepted_event_id != change.event_id:
        raise ValueError("result last event does not match change")
    if result.provider_id != change.source_id:
        raise ValueError("result provider does not match change")
    if result.market_id != change.market.canonical_id:
        raise ValueError("result market does not match change")

    expected_evidence = make_canonical_market_state_observation(change)
    evidence_id = expected_evidence.get_canonical_id()
    retained_evidence = ledger.get(evidence_id)
    if retained_evidence is None:
        raise ValueError("canonical observation is missing from Ledger")
    if canonicalize(retained_evidence.canonical_dict()) != canonicalize(
        expected_evidence.canonical_dict()
    ):
        raise ValueError("retained observation does not match canonical change")

    checkpoint = checkpoint_store.load()
    if result.final_checkpoint_id != checkpoint.checkpoint_id:
        raise ValueError("result checkpoint does not match persisted checkpoint")
    if checkpoint.provider_id != change.source_id:
        raise ValueError("checkpoint provider does not match change")
    if checkpoint.market.canonical_id != change.market.canonical_id:
        raise ValueError("checkpoint market does not match change")
    if checkpoint.cursor.ordering_key != (
        change.chain_sequence,
        change.event_index,
    ):
        raise ValueError("checkpoint cursor does not match change")

    payload: dict[str, str | int] = {
        "accepted_count": result.accepted_count,
        "checkpoint_id": checkpoint.checkpoint_id,
        "event_id": change.event_id,
        "evidence_id": evidence_id,
        "ledger_content_hash": _require_sha256(
            ledger.content_hash,
            "ledger.content_hash",
        ),
        "market_id": result.market_id,
        "provider_id": result.provider_id,
        "schema_version": _SCHEMA_VERSION,
        "session_id": result.session_id,
        "source_event_id": change.source_event_id,
    }
    return DurableIngestionCommitReceipt(
        receipt_id=deterministic_id("durable_ingestion_commit", payload),
        session_id=result.session_id,
        provider_id=result.provider_id,
        market_id=result.market_id,
        event_id=change.event_id,
        source_event_id=change.source_event_id,
        evidence_id=evidence_id,
        ledger_content_hash=payload["ledger_content_hash"],
        checkpoint_id=checkpoint.checkpoint_id,
        accepted_count=result.accepted_count,
    )


__all__ = [
    "ContentHashedEvidenceLedger",
    "DurableIngestionCommitReceipt",
    "create_durable_ingestion_commit_receipt",
]
