from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


def _require_non_empty_string(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True)
class DomainEventEnvelope:
    event_id: str
    event_type: str
    occurred_at: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty_string(self.event_id, "event_id")
        _require_non_empty_string(self.event_type, "event_type")
        _require_non_empty_string(self.occurred_at, "occurred_at")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }
