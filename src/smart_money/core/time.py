from __future__ import annotations

from datetime import datetime, timezone


def ensure_utc_datetime(value: datetime) -> datetime:
    """Return an aware UTC datetime or raise ValueError.

    This function intentionally never reads wall-clock time.
    """
    if not isinstance(value, datetime):
        raise TypeError("value must be a datetime")

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")

    return value.astimezone(timezone.utc)


def datetime_to_canonical(value: datetime) -> str:
    """Serialize a datetime as canonical UTC ISO-8601 with Z suffix."""
    utc_value = ensure_utc_datetime(value)

    if utc_value.microsecond:
        text = utc_value.isoformat(timespec="microseconds")
    else:
        text = utc_value.isoformat(timespec="seconds")

    return text.replace("+00:00", "Z")
