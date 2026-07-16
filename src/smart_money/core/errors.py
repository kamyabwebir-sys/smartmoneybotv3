from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


def _require_non_empty_string(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


@dataclass(frozen=True)
class DomainError:
    code: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty_string(self.code, "code")
        _require_non_empty_string(self.message, "message")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": dict(self.details),
        }
