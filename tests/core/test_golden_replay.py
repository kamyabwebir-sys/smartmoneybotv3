import dataclasses

from smart_money.core.replay import BaselineReplayPack, GoldenReplayFixture


class TestContractCompliance:
    def test_golden_replay_fixture_uses_slots(self):
        assert not hasattr(GoldenReplayFixture, "__dict__") or "__slots__" in dir(GoldenReplayFixture)
        assert GoldenReplayFixture.__dataclass_params__.frozen is True
        assert getattr(GoldenReplayFixture, "__slots__", None) is not None

    def test_baseline_replay_pack_uses_slots(self):
        assert BaselineReplayPack.__dataclass_params__.frozen is True
        assert getattr(BaselineReplayPack, "__slots__", None) is not None

    def test_baseline_replay_pack_field_order(self):
        names = [f.name for f in dataclasses.fields(BaselineReplayPack)]
        assert names == [
            "pack_id",
            "pipeline_version",
            "config_hash",
            "fixtures",
            "creation_timestamp",
        ]

    def test_baseline_replay_pack_fixtures_annotation(self):
        field = {f.name: f for f in dataclasses.fields(BaselineReplayPack)}["fixtures"]
        assert field.type in ("tuple[str, ...]", tuple[str, ...])


# ---------------------------------------------------------------------------
# Slice 0.8 contract-compliance tests (appended)
# ---------------------------------------------------------------------------
import dataclasses as _dc

from smart_money.core.replay import BaselineReplayPack, GoldenReplayFixture


class TestSlice08ContractCompliance:
    def test_golden_replay_fixture_uses_slots(self):
        assert GoldenReplayFixture.__dataclass_params__.frozen is True
        assert getattr(GoldenReplayFixture, "__slots__", None) is not None

    def test_baseline_replay_pack_uses_slots(self):
        assert BaselineReplayPack.__dataclass_params__.frozen is True
        assert getattr(BaselineReplayPack, "__slots__", None) is not None

    def test_baseline_replay_pack_field_order(self):
        names = [f.name for f in _dc.fields(BaselineReplayPack)]
        assert names == [
            "pack_id",
            "pipeline_version",
            "config_hash",
            "fixtures",
            "creation_timestamp",
        ]

    def test_baseline_replay_pack_fixtures_annotation(self):
        field = {f.name: f for f in _dc.fields(BaselineReplayPack)}["fixtures"]
        assert field.type in ("tuple[str, ...]", tuple[str, ...])