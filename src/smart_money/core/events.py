from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .frozen import deep_freeze, deep_thaw


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string")
    return normalized


@dataclass(frozen=True, slots=True)
class DomainEventEnvelope:
    event_id: str
    event_type: str
    occurred_at: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "event_id",
            _require_non_empty_string(self.event_id, "event_id"),
        )
        object.__setattr__(
            self,
            "event_type",
            _require_non_empty_string(self.event_type, "event_type"),
        )
        object.__setattr__(
            self,
            "occurred_at",
            _require_non_empty_string(self.occurred_at, "occurred_at"),
        )

        if not isinstance(self.payload, Mapping):
            raise TypeError("payload must be a mapping")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(self, "payload", deep_freeze(self.payload, "payload"))
        object.__setattr__(self, "metadata", deep_freeze(self.metadata, "metadata"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "payload": deep_thaw(self.payload),
            "metadata": deep_thaw(self.metadata),
        }
