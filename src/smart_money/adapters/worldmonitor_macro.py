from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)

_SOURCE_ID = "worldmonitor"
_EXPECTED_KEYS = {
    "metric",
    "observed_at",
    "value",
    "unit",
    "status",
    "source_revision",
}


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _decimal(value: object) -> Decimal:
    if isinstance(value, bool):
        raise TypeError("value must be Decimal-compatible")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("value must be Decimal-compatible") from None
    if not result.is_finite():
        raise ValueError("value must be finite")
    return result


class WorldMonitorMacroAdapter:
    """Strict, offline parser for a captured World Monitor observation."""

    source_id = _SOURCE_ID

    @classmethod
    def from_payload(
        cls,
        payload: Mapping[str, Any],
    ) -> MacroEvidenceObservation:
        if not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping")
        if set(payload) != _EXPECTED_KEYS:
            raise ValueError("payload keys do not match World Monitor contract")
        observed_at = payload["observed_at"]
        if isinstance(observed_at, bool) or not isinstance(observed_at, int):
            raise TypeError("observed_at must be an integer")
        if observed_at < 0:
            raise ValueError("observed_at must be non-negative")
        status_value = _required_text(payload["status"], "status")
        try:
            status = MacroObservationStatus(status_value.upper())
        except ValueError:
            raise ValueError("unsupported World Monitor observation status") from None
        return MacroEvidenceObservation(
            source_id=cls.source_id,
            metric=_required_text(payload["metric"], "metric"),
            observed_at=observed_at,
            value=_decimal(payload["value"]),
            unit=_required_text(payload["unit"], "unit"),
            status=status,
            source_revision=_required_text(
                payload["source_revision"],
                "source_revision",
            ),
        )


__all__ = ["WorldMonitorMacroAdapter"]
