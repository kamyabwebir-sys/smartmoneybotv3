from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from smart_money.core.ids import deterministic_id


class IngestionEnvelopeError(ValueError):
    """Raised when an ingestion envelope violates the evidence boundary."""


_ALLOWED_SCALAR_TYPES = (str, int, bool, type(None))


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise IngestionEnvelopeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise IngestionEnvelopeError(f"{field_name} must be non-empty")

    return normalized


def freeze_evidence_value(value: Any, field_name: str = "value") -> Any:
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key in value:
            if not isinstance(key, str):
                raise IngestionEnvelopeError(f"{field_name} keys must be strings")

            normalized_key = key.strip()
            if not normalized_key:
                raise IngestionEnvelopeError(
                    f"{field_name} keys must be non-empty strings"
                )
            if normalized_key in frozen:
                raise IngestionEnvelopeError(
                    f"{field_name} contains duplicate normalized keys"
                )

            frozen[normalized_key] = freeze_evidence_value(
                value[key], f"{field_name}.{normalized_key}"
            )

        return MappingProxyType(dict(sorted(frozen.items())))

    if isinstance(value, (list, tuple)):
        return tuple(freeze_evidence_value(item, field_name) for item in value)

    if isinstance(value, _ALLOWED_SCALAR_TYPES):
        return value

    raise IngestionEnvelopeError(f"{field_name} contains unsupported value type")


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(value[key]) for key in sorted(value.keys())}

    if isinstance(value, tuple):
        return [_plain(item) for item in value]

    return value


@dataclass(frozen=True, slots=True)
class IngestionEnvelope:
    """Validated immutable evidence ingestion envelope.

    The envelope stores evidence facts only. It does not trade, score risk,
    infer decisions, call networks, read files, or perform ML classification.
    """

    source: str
    symbol: str
    payload: Mapping[str, Any]
    metadata: Mapping[str, Any]
    schema_version: str = "ingestion_envelope.v1"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _require_text(self.schema_version, "schema_version")
        )
        object.__setattr__(self, "source", _require_text(self.source, "source"))
        object.__setattr__(self, "symbol", _require_text(self.symbol, "symbol"))

        if not isinstance(self.payload, Mapping):
            raise IngestionEnvelopeError("payload must be a mapping")
        if not isinstance(self.metadata, Mapping):
            raise IngestionEnvelopeError("metadata must be a mapping")

        object.__setattr__(
            self, "payload", freeze_evidence_value(self.payload, "payload")
        )
        object.__setattr__(
            self, "metadata", freeze_evidence_value(self.metadata, "metadata")
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "metadata": _plain(self.metadata),
            "payload": _plain(self.payload),
            "schema_version": self.schema_version,
            "source": self.source,
            "symbol": self.symbol,
        }

    def deterministic_id(self) -> str:
        return deterministic_id("ingestion_envelope", self.canonical_dict())

    def as_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "id": self.deterministic_id(),
                "metadata": self.metadata,
                "payload": self.payload,
                "schema_version": self.schema_version,
                "source": self.source,
                "symbol": self.symbol,
            }
        )
