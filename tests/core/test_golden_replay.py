from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from smart_money.core.replay import (
    BaselineReplayPack,
    GoldenReplayFixture,
    create_baseline_replay_pack,
    create_golden_replay_fixture,
)


def _fixture(*, data_hash: str = "data-hash") -> GoldenReplayFixture:
    return create_golden_replay_fixture(
        replay_manifest_id="manifest-id",
        timestamp=datetime(2026, 1, 1, 3, tzinfo=timezone(timedelta(hours=3))),
        data_hash=data_hash,
        metadata={"b": 2, "a": 1},
    )


def test_golden_replay_fixture_contract_shape() -> None:
    assert GoldenReplayFixture.__dataclass_params__.frozen is True
    assert getattr(GoldenReplayFixture, "__slots__", None) is not None


def test_baseline_replay_pack_contract_shape() -> None:
    assert BaselineReplayPack.__dataclass_params__.frozen is True
    assert getattr(BaselineReplayPack, "__slots__", None) is not None
    assert [field.name for field in dataclasses.fields(BaselineReplayPack)] == [
        "pack_id",
        "pipeline_version",
        "config_hash",
        "fixtures",
        "creation_timestamp",
    ]
    fixtures_field = {
        field.name: field for field in dataclasses.fields(BaselineReplayPack)
    }["fixtures"]
    assert fixtures_field.type in ("tuple[str, ...]", tuple[str, ...])


def test_fixture_factory_is_canonical_and_normalizes_utc() -> None:
    first = _fixture()
    second = _fixture()

    assert first == second
    assert first.timestamp == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert first.metadata_json == '{"a":1,"b":2}'


def test_fixture_rejects_forged_identity_and_noncanonical_metadata() -> None:
    valid = _fixture()

    with pytest.raises(ValueError, match="fixture_id"):
        GoldenReplayFixture(
            fixture_id="forged",
            replay_manifest_id=valid.replay_manifest_id,
            timestamp=valid.timestamp,
            data_hash=valid.data_hash,
            metadata_json=valid.metadata_json,
        )

    with pytest.raises(ValueError, match="canonical JSON"):
        GoldenReplayFixture(
            fixture_id=valid.fixture_id,
            replay_manifest_id=valid.replay_manifest_id,
            timestamp=valid.timestamp,
            data_hash=valid.data_hash,
            metadata_json='{"b": 2, "a": 1}',
        )


def test_pack_identity_is_order_independent_and_rejects_duplicates() -> None:
    first_fixture = _fixture(data_hash="first")
    second_fixture = _fixture(data_hash="second")
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    first = create_baseline_replay_pack(
        "pipeline-v1",
        "config-hash",
        (second_fixture, first_fixture),
        timestamp,
    )
    second = create_baseline_replay_pack(
        "pipeline-v1",
        "config-hash",
        (first_fixture, second_fixture),
        timestamp,
    )

    assert first.pack_id == second.pack_id
    assert first.fixtures == tuple(sorted(first.fixtures))

    with pytest.raises(ValueError, match="duplicate"):
        create_baseline_replay_pack(
            "pipeline-v1",
            "config-hash",
            (first_fixture, first_fixture),
            timestamp,
        )


def test_pack_rejects_forged_identity() -> None:
    fixture = _fixture()

    with pytest.raises(ValueError, match="pack_id"):
        BaselineReplayPack(
            pack_id="forged",
            pipeline_version="pipeline-v1",
            config_hash="config-hash",
            fixtures=(fixture.fixture_id,),
            creation_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
