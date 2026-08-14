from pathlib import Path

import pytest

from contracts import EvidencePayload
from ledger import EvidenceGroundingLedger
from smart_money.application.replay import ReplayEngine as CanonicalReplayEngine


def test_replay_engine_emits_persisted_data(tmp_path):
    # 1. Create a dummy ledger file
    ledger = EvidenceGroundingLedger()
    p1 = EvidencePayload("SRC-1", "market_structure", 100, {"price": 10})
    p2 = EvidencePayload("SRC-1", "market_structure", 101, {"price": 20})
    ledger.record(p1)
    ledger.record(p2)

    file_path = tmp_path / "test_ledger.json"
    ledger.save_to_disk(file_path)

    # 2. Initialize Replay Engine
    engine = CanonicalReplayEngine(file_path)

    # 3. Verify
    assert engine.entry_count == 2
    emitted = list(engine.stream_captured_evidence())

    assert len(emitted) == 2
    assert emitted[0].timestamp == 100
    assert emitted[1].timestamp == 101
    assert emitted[0].data["price"] == 10


def test_replay_engine_fails_closed_without_persisted_ledger(tmp_path: Path):
    missing_path = tmp_path / "missing-ledger.json"

    with pytest.raises(FileNotFoundError, match="persisted ledger not found"):
        CanonicalReplayEngine(missing_path)
