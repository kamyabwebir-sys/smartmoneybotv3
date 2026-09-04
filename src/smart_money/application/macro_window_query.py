from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from smart_money.application.macro_evidence_projection import (
    ExternalMacroEvidenceProjection,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)


@dataclass(frozen=True, slots=True)
class MacroEvidenceWindow:
    """Deterministic, immutable result for one bounded macro query."""

    metric: str
    start_at: int
    end_at: int
    observations: tuple[MacroEvidenceObservation, ...]
    conflicted_count: int
    unknown_count: int

    @property
    def missing(self) -> bool:
        return not self.observations

    @property
    def matched_count(self) -> int:
        return len(self.observations)


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


def _observation_from_payload(
    payload: Any,
) -> MacroEvidenceObservation:
    if payload.evidence_type != ExternalMacroEvidenceProjection.EVIDENCE_TYPE:
        raise ValueError("unsupported macro evidence type")
    data = _mapping(payload.data.get("macro_observation"), "macro_observation")
    status_value = data.get("status")
    try:
        status = MacroObservationStatus(status_value)
    except (TypeError, ValueError):
        raise ValueError("macro observation status is invalid") from None
    observation = MacroEvidenceObservation(
        source_id=payload.source_id,
        metric=data.get("metric"),
        observed_at=data.get("observed_at"),
        value=data.get("value"),
        unit=data.get("unit"),
        status=status,
        source_revision=data.get("source_revision"),
        schema_version=data.get("schema_version"),
    )
    if payload.timestamp != observation.observed_at:
        raise ValueError("macro payload timestamp does not match observation")
    if data.get("canonical_id") != observation.canonical_id:
        raise ValueError("macro payload canonical_id does not match observation")
    ExternalMacroEvidenceProjection(
        payload=payload,
        observation_id=observation.canonical_id,
    )
    return observation


def query_macro_evidence_window(
    ledger: EvidenceLedger,
    *,
    metric: str,
    start_at: int,
    end_at: int,
) -> MacroEvidenceWindow:
    """Query external macro Evidence deterministically from the Ledger."""
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    if not isinstance(metric, str) or not metric.strip():
        raise ValueError("metric must be a non-empty string")
    if isinstance(start_at, bool) or not isinstance(start_at, int):
        raise TypeError("start_at must be an integer")
    if isinstance(end_at, bool) or not isinstance(end_at, int):
        raise TypeError("end_at must be an integer")
    if start_at < 0 or end_at < 0:
        raise ValueError("query bounds must be non-negative")
    if start_at > end_at:
        raise ValueError("start_at must not exceed end_at")

    selected: dict[str, MacroEvidenceObservation] = {}
    for payload in ledger.iter_payloads():
        if payload.evidence_type != ExternalMacroEvidenceProjection.EVIDENCE_TYPE:
            continue
        observation = _observation_from_payload(payload)
        if (
            observation.metric == metric.strip()
            and start_at <= observation.observed_at <= end_at
        ):
            selected[observation.canonical_id] = observation

    observations = tuple(
        sorted(
            selected.values(),
            key=lambda item: (item.observed_at, item.canonical_id),
        )
    )
    return MacroEvidenceWindow(
        metric=metric.strip(),
        start_at=start_at,
        end_at=end_at,
        observations=observations,
        conflicted_count=sum(
            item.status is MacroObservationStatus.CONFLICTED
            for item in observations
        ),
        unknown_count=sum(
            item.status is MacroObservationStatus.UNKNOWN
            for item in observations
        ),
    )


__all__ = ["MacroEvidenceWindow", "query_macro_evidence_window"]
