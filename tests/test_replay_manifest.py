from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from smart_money.core.replay import ReplayManifest, make_replay_manifest
from smart_money.core.serialization import canonical_json


def test_replay_manifest_id_is_stable() -> None:
    first = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
        symbol="SOLUSDT",
        venue="binance",
        timeframe="1m",
        subject_ids=("b", "a"),
        notes="stable-note",
    )
    second = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
        symbol="SOLUSDT",
        venue="binance",
        timeframe="1m",
        subject_ids=("a", "b"),
        notes="stable-note",
    )

    assert first.manifest_id == second.manifest_id


def test_replay_manifest_id_changes_when_config_hash_changes() -> None:
    first = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
    )
    second = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_002",
    )

    assert first.manifest_id != second.manifest_id


def test_replay_manifest_id_changes_when_dataset_hash_changes() -> None:
    first = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
    )
    second = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_002",
        config_hash="config_hash_001",
    )

    assert first.manifest_id != second.manifest_id


def test_replay_manifest_requires_aware_datetimes() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        make_replay_manifest(
            pipeline_version="pipeline.v1",
            input_dataset_hash="dataset_hash_001",
            config_hash="config_hash_001",
            range_start=datetime(2024, 1, 1, 0, 0),
        )


def test_replay_manifest_normalizes_to_utc() -> None:
    manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
        range_start=datetime(2024, 1, 1, 3, 30, tzinfo=timezone(timedelta(hours=3, minutes=30))),
        range_end=datetime(2024, 1, 1, 4, 30, tzinfo=timezone(timedelta(hours=3, minutes=30))),
    )

    assert manifest.range_start == datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert manifest.range_end == datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc)


def test_range_start_must_not_exceed_range_end() -> None:
    with pytest.raises(ValueError, match="range_start"):
        make_replay_manifest(
            pipeline_version="pipeline.v1",
            input_dataset_hash="dataset_hash_001",
            config_hash="config_hash_001",
            range_start=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc),
            range_end=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        )


def test_replay_manifest_is_immutable() -> None:
    manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
    )

    with pytest.raises(FrozenInstanceError):
        manifest.symbol = "BTCUSDT"  # type: ignore[misc]


def test_manual_wrong_manifest_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="manifest_id"):
        ReplayManifest(
            manifest_id="replay_manifest_wrong",
            pipeline_version="pipeline.v1",
            input_dataset_hash="dataset_hash_001",
            config_hash="config_hash_001",
        )


def test_canonical_serialization_for_replay_manifest_is_stable() -> None:
    manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash="dataset_hash_001",
        config_hash="config_hash_001",
        symbol="SOLUSDT",
        venue="base",
        timeframe="5m",
        subject_ids=("subject_b", "subject_a"),
        notes="stable-note",
    )

    first = canonical_json(manifest.canonical_dict())
    second = canonical_json(manifest.canonical_dict())

    assert first == second
