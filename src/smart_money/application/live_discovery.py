from __future__ import annotations
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload
import json
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LiveProviderSession:
    provider_id: str
    session_id: str
    started_slot: int
    schema_version: str = "live_provider_session.v1"

    def __post_init__(self) -> None:
        if not self.provider_id.strip() or self.started_slot < 0:
            raise ValueError("invalid live session")
        if self.session_id != deterministic_id(
            "live_provider_session",
            {
                "provider_id": self.provider_id.strip(),
                "schema_version": self.schema_version,
                "started_slot": self.started_slot,
            },
        ):
            raise ValueError("session_id mismatch")


def start_live_session(provider_id: str, started_slot: int) -> LiveProviderSession:
    identity = {
        "provider_id": provider_id.strip(),
        "schema_version": "live_provider_session.v1",
        "started_slot": started_slot,
    }
    return LiveProviderSession(
        provider_id, deterministic_id("live_provider_session", identity), started_slot
    )


def poll_solana_boundary(
    fetcher: Callable[..., Mapping[str, Any]], cursor: int
) -> Mapping[str, Any]:
    if not callable(fetcher) or isinstance(cursor, bool) or cursor < 0:
        raise ValueError("invalid polling boundary")
    parameters = inspect.signature(fetcher).parameters.values()
    accepts_rpc_request = any(
        parameter.kind
        in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
        for parameter in parameters
    ) or sum(
        parameter.kind
        in {inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}
        for parameter in parameters
    ) >= 2
    if accepts_rpc_request:
        result = fetcher(
            "getSlot",
            {"commitment": "confirmed", "minContextSlot": cursor},
        )
    else:
        result = fetcher(cursor)
    if not isinstance(result, Mapping):
        raise TypeError("poll result must be mapping")
    return result


@dataclass(frozen=True, slots=True)
class LiveObservationCheckpoint:
    session_id: str
    slot: int
    checkpoint_id: str
    schema_version: str = "live_observation_checkpoint.v1"

    def __post_init__(self) -> None:
        if self.slot < 0 or self.checkpoint_id != deterministic_id(
            "live_observation_checkpoint",
            {
                "schema_version": self.schema_version,
                "session_id": self.session_id,
                "slot": self.slot,
            },
        ):
            raise ValueError("checkpoint mismatch")


def checkpoint_session(
    session: LiveProviderSession, slot: int
) -> LiveObservationCheckpoint:
    return LiveObservationCheckpoint(
        session.session_id,
        slot,
        deterministic_id(
            "live_observation_checkpoint",
            {
                "schema_version": "live_observation_checkpoint.v1",
                "session_id": session.session_id,
                "slot": slot,
            },
        ),
    )


def ingest_live_activity(
    kind: str, data: Mapping[str, Any], slot: int
) -> EvidencePayload:
    if kind not in {"wallet_activity", "token_discovery"} or not data:
        raise ValueError("unsupported live activity")
    return EvidencePayload(
        source_id="live-solana",
        evidence_type=f"live_{kind}",
        timestamp=slot,
        data={"activity": dict(data)},
        metadata={
            "authority": "EXTERNAL_NON_AUTHORITATIVE",
            "classification": "EVIDENCE",
            "verification_status": "UNKNOWN",
            "provenance": {"slot": str(slot)},
        },
    )


@dataclass(frozen=True, slots=True)
class LiveProviderFailureEvidence:
    provider_id: str
    operation: str
    retry_count: int
    evidence_id: str
    schema_version: str = "live_provider_failure.v1"

    def __post_init__(self) -> None:
        if (
            self.retry_count < 0
            or not self.provider_id.strip()
            or not self.operation.strip()
        ):
            raise ValueError("invalid failure evidence")
        if self.evidence_id != deterministic_id(
            "live_provider_failure",
            {
                "operation": self.operation.strip(),
                "provider_id": self.provider_id.strip(),
                "retry_count": self.retry_count,
                "schema_version": self.schema_version,
            },
        ):
            raise ValueError("evidence_id mismatch")


def build_live_candidate_payload(
    candidate: Mapping[str, Any], slot: int
) -> EvidencePayload:
    if not candidate:
        raise ValueError("candidate must be non-empty")
    return EvidencePayload(
        source_id="live-discovery",
        evidence_type="live_candidate",
        timestamp=slot,
        data={"candidate": dict(candidate)},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
            "provenance": {"source": "live"},
        },
    )


@dataclass(frozen=True, slots=True)
class LiveDiscoveryReplaySession:
    session_id: str
    checkpoint_ids: tuple[str, ...]
    replay_id: str
    schema_version: str = "live_discovery_replay.v1"

    def __post_init__(self) -> None:
        if self.replay_id != deterministic_id(
            "live_discovery_replay",
            {
                "checkpoint_ids": self.checkpoint_ids,
                "schema_version": self.schema_version,
                "session_id": self.session_id,
            },
        ):
            raise ValueError("replay_id mismatch")


@dataclass(frozen=True, slots=True)
class LiveDiscoveryDashboardReadModel:
    session: LiveProviderSession
    checkpoints: tuple[LiveObservationCheckpoint, ...]
    candidates: tuple[EvidencePayload, ...]
    schema_version: str = "live_discovery_dashboard.v1"


class LiveSessionStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items = {}

    def save(self, session: LiveProviderSession) -> str:
        self._items[session.session_id] = session
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "items": [
                        {
                            "provider_id": x.provider_id,
                            "session_id": x.session_id,
                            "started_slot": x.started_slot,
                        }
                        for x in self._items.values()
                    ]
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return session.session_id

    def get(self, session_id: str) -> LiveProviderSession | None:
        return self._items.get(session_id)


class CheckpointStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items = {}

    def save(self, checkpoint: LiveObservationCheckpoint) -> str:
        self._items[checkpoint.checkpoint_id] = checkpoint
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "items": [
                        {
                            "session_id": x.session_id,
                            "slot": x.slot,
                            "checkpoint_id": x.checkpoint_id,
                        }
                        for x in self._items.values()
                    ]
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return checkpoint.checkpoint_id

    def get(self, checkpoint_id: str) -> LiveObservationCheckpoint | None:
        return self._items.get(checkpoint_id)


def verify_checkpoint_recovery(
    checkpoint: LiveObservationCheckpoint, store: CheckpointStore
) -> bool:
    return store.get(checkpoint.checkpoint_id) == checkpoint


def bind_live_evidence(ledger: Any, payload: EvidencePayload) -> str:
    if not isinstance(payload, EvidencePayload):
        raise TypeError("payload must be EvidencePayload")
    evidence_id = payload.get_canonical_id()
    if ledger.append(payload) != evidence_id:
        raise ValueError("ledger identity mismatch")
    return evidence_id


def verify_live_candidate_replay(
    payload: EvidencePayload, replayed: EvidencePayload
) -> bool:
    return payload.get_canonical_id() == replayed.get_canonical_id()


@dataclass(frozen=True, slots=True)
class ProviderRetryPolicy:
    max_retries: int
    backoff_slots: int

    def __post_init__(self) -> None:
        if self.max_retries < 0 or self.backoff_slots < 0:
            raise ValueError("retry values must be non-negative")


@dataclass(frozen=True, slots=True)
class LiveDiscoveryHealthDashboard:
    session_id: str
    checkpoint_count: int
    candidate_count: int
    healthy: bool


def build_live_health_dashboard(
    model: LiveDiscoveryDashboardReadModel,
) -> LiveDiscoveryHealthDashboard:
    return LiveDiscoveryHealthDashboard(
        model.session.session_id,
        len(model.checkpoints),
        len(model.candidates),
        bool(model.checkpoints),
    )


@dataclass(frozen=True, slots=True)
class SolanaProductionConnector:
    provider_id: str = "solana-production"

    def fetch(
        self, fetcher: Callable[[int], Mapping[str, Any]], cursor: int
    ) -> Mapping[str, Any]:
        return poll_solana_boundary(fetcher, cursor)


__all__ = [
    "LiveProviderSession",
    "start_live_session",
    "poll_solana_boundary",
    "LiveObservationCheckpoint",
    "checkpoint_session",
    "ingest_live_activity",
    "LiveProviderFailureEvidence",
    "build_live_candidate_payload",
    "LiveDiscoveryReplaySession",
    "LiveDiscoveryDashboardReadModel",
    "LiveSessionStore",
    "CheckpointStore",
    "verify_checkpoint_recovery",
    "bind_live_evidence",
    "verify_live_candidate_replay",
    "ProviderRetryPolicy",
    "LiveDiscoveryHealthDashboard",
    "build_live_health_dashboard",
    "SolanaProductionConnector",
]
