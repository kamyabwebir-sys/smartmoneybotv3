import pytest

from smart_money.adapters.persistence.solana_slot_cursor_store import (
    JsonSolanaSlotCursorStore,
)
from smart_money.domain.solana_observation import SolanaChainObservation, SolanaSlotCursor


def test_cursor_store_round_trips_and_returns_deterministic_id(tmp_path):
    path = tmp_path / "cursor.json"
    cursor = SolanaSlotCursor.from_observation(
        SolanaChainObservation(10, 100, "sig", "program", "wallet")
    )
    first = JsonSolanaSlotCursorStore(path)
    assert first.save(cursor) == cursor.canonical_id
    second = JsonSolanaSlotCursorStore(path)
    assert second.load() == cursor
    assert second.cursor_id == cursor.canonical_id


def test_cursor_store_rejects_wrong_type(tmp_path):
    with pytest.raises(TypeError, match="SolanaSlotCursor"):
        JsonSolanaSlotCursorStore(tmp_path / "cursor.json").save(object())  # type: ignore[arg-type]


def test_cursor_store_replay_verifies_persisted_cursor(tmp_path):
    path = tmp_path / "cursor.json"
    observation = SolanaChainObservation(10, 100, "sig", "program", "wallet")
    store = JsonSolanaSlotCursorStore(path)
    store.save(SolanaSlotCursor.from_observation(observation))
    receipt = store.replay(observation)
    assert receipt.matches is True
    assert receipt.stored_cursor_id == receipt.replayed_cursor_id


def test_cursor_store_replay_fails_on_mismatch(tmp_path):
    path = tmp_path / "cursor.json"
    store = JsonSolanaSlotCursorStore(path)
    store.save(
        SolanaSlotCursor.from_observation(
            SolanaChainObservation(10, 100, "sig", "program", "wallet")
        )
    )
    with pytest.raises(ValueError, match="does not match"):
        store.replay(SolanaChainObservation(11, 101, "next", "program", "wallet"))
