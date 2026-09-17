from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .ids import deterministic_id
from .time import ensure_utc_datetime


def _require_non_empty_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")

    return normalized


def _require_optional_text(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_text(value, field_name)


def _normalize_subject_ids(value: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError("subject_ids must be a tuple")

    normalized: list[str] = []
    for item in value:
        normalized.append(_require_non_empty_text(item, "subject_ids"))

    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True)
class ReplayManifest:
    manifest_id: str
    pipeline_version: str
    input_dataset_hash: str
    config_hash: str
    symbol: str | None = None
    venue: str | None = None
    timeframe: str | None = None
    range_start: datetime | None = None
    range_end: datetime | None = None
    subject_ids: tuple[str, ...] = ()
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "manifest_id", _require_non_empty_text(self.manifest_id, "manifest_id"))
        object.__setattr__(self, "pipeline_version", _require_non_empty_text(self.pipeline_version, "pipeline_version"))
        object.__setattr__(self, "input_dataset_hash", _require_non_empty_text(self.input_dataset_hash, "input_dataset_hash"))
        object.__setattr__(self, "config_hash", _require_non_empty_text(self.config_hash, "config_hash"))

        object.__setattr__(self, "symbol", _require_optional_text(self.symbol, "symbol"))
        object.__setattr__(self, "venue", _require_optional_text(self.venue, "venue"))
        object.__setattr__(self, "timeframe", _require_optional_text(self.timeframe, "timeframe"))
        object.__setattr__(self, "notes", _require_optional_text(self.notes, "notes"))

        if self.range_start is not None:
            object.__setattr__(self, "range_start", ensure_utc_datetime(self.range_start))
        if self.range_end is not None:
            object.__setattr__(self, "range_end", ensure_utc_datetime(self.range_end))

        if self.range_start is not None and self.range_end is not None:
            if self.range_start > self.range_end:
                raise ValueError("range_start must be less than or equal to range_end")

        object.__setattr__(self, "subject_ids", _normalize_subject_ids(self.subject_ids))

        expected_manifest_id = deterministic_id("replay_manifest", self.identity_payload())
        if self.manifest_id != expected_manifest_id:
            raise ValueError("manifest_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "pipeline_version": self.pipeline_version,
            "input_dataset_hash": self.input_dataset_hash,
            "config_hash": self.config_hash,
            "symbol": self.symbol,
            "venue": self.venue,
            "timeframe": self.timeframe,
            "range_start": self.range_start,
            "range_end": self.range_end,
            "subject_ids": self.subject_ids,
            "notes": self.notes,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            **self.identity_payload(),
        }


def make_replay_manifest(
    *,
    pipeline_version: str,
    input_dataset_hash: str,
    config_hash: str,
    symbol: str | None = None,
    venue: str | None = None,
    timeframe: str | None = None,
    range_start: datetime | None = None,
    range_end: datetime | None = None,
    subject_ids: tuple[str, ...] = (),
    notes: str | None = None,
) -> ReplayManifest:
    normalized_range_start = ensure_utc_datetime(range_start) if range_start is not None else None
    normalized_range_end = ensure_utc_datetime(range_end) if range_end is not None else None

    payload = {
        "pipeline_version": _require_non_empty_text(pipeline_version, "pipeline_version"),
        "input_dataset_hash": _require_non_empty_text(input_dataset_hash, "input_dataset_hash"),
        "config_hash": _require_non_empty_text(config_hash, "config_hash"),
        "symbol": _require_optional_text(symbol, "symbol"),
        "venue": _require_optional_text(venue, "venue"),
        "timeframe": _require_optional_text(timeframe, "timeframe"),
        "range_start": normalized_range_start,
        "range_end": normalized_range_end,
        "subject_ids": _normalize_subject_ids(subject_ids),
        "notes": _require_optional_text(notes, "notes"),
    }

    manifest_id = deterministic_id("replay_manifest", payload)

    return ReplayManifest(
        manifest_id=manifest_id,
        pipeline_version=pipeline_version,
        input_dataset_hash=input_dataset_hash,
        config_hash=config_hash,
        symbol=symbol,
        venue=venue,
        timeframe=timeframe,
        range_start=range_start,
        range_end=range_end,
        subject_ids=subject_ids,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Slice 0.8 - Golden Replay Fixtures / Baseline Replay Pack (appended)
# ---------------------------------------------------------------------------
from dataclasses import dataclass as _s08_dataclass
from datetime import datetime as _s08_datetime
from typing import Iterable as _S08Iterable, Union as _S08Union

from smart_money.core.ids import deterministic_id as _s08_deterministic_id
from smart_money.core.serialization import canonical_json as _s08_canonical_json
from smart_money.core.time import ensure_utc_datetime as _s08_ensure_utc_datetime


@_s08_dataclass(frozen=True, slots=True)
class GoldenReplayFixture:
    fixture_id: str
    replay_manifest_id: str
    timestamp: _s08_datetime
    data_hash: str
    metadata_json: str


@_s08_dataclass(frozen=True, slots=True)
class BaselineReplayPack:
    pack_id: str
    pipeline_version: str
    config_hash: str
    fixtures: tuple[str, ...]
    creation_timestamp: _s08_datetime


def create_golden_replay_fixture(
    replay_manifest_id: str,
    timestamp: _s08_datetime,
    data_hash: str,
    metadata: dict,
) -> GoldenReplayFixture:
    utc_ts = _s08_ensure_utc_datetime(timestamp)
    meta_json = _s08_canonical_json(metadata)
    fid = _s08_deterministic_id(
        "golden_replay_fixture",
        {
            "replay_manifest_id": replay_manifest_id,
            "timestamp": utc_ts.isoformat(),
            "data_hash": data_hash,
            "metadata_json": meta_json,
        },
    )
    return GoldenReplayFixture(
        fixture_id=fid,
        replay_manifest_id=replay_manifest_id,
        timestamp=utc_ts,
        data_hash=data_hash,
        metadata_json=meta_json,
    )


def create_baseline_replay_pack(
    pipeline_version: str,
    config_hash: str,
    fixtures: "_S08Iterable[_S08Union[GoldenReplayFixture, str]]",
    creation_timestamp: _s08_datetime,
) -> BaselineReplayPack:
    ids = [
        f.fixture_id if isinstance(f, GoldenReplayFixture) else f
        for f in fixtures
    ]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate fixture_id values are not allowed")
    sorted_ids = tuple(sorted(ids))
    pid = _s08_deterministic_id(
        "baseline_replay_pack",
        {
            "pipeline_version": pipeline_version,
            "config_hash": config_hash,
            "fixtures": list(sorted_ids),
        },
    )
    return BaselineReplayPack(
        pack_id=pid,
        pipeline_version=pipeline_version,
        config_hash=config_hash,
        fixtures=sorted_ids,
        creation_timestamp=_s08_ensure_utc_datetime(creation_timestamp),
    )