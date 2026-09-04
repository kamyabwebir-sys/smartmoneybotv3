import pytest

from smart_money.adapters.persistence.solana_slot_cursor_store import (
    JsonSolanaSlotCursorStore,
)
from smart_money.application.solana_cursor_advance_binding import (
    advance_and_persist_solana_cursor,
    verify_solana_cursor_advance_replay,
)
from smart_money.domain.solana_observation import SolanaChainObservation


def _observation(slot: int, signature: str):
    return SolanaChainObservation(slot, slot * 10, signature, "program", "wallet")


def test_advance_persists_and_returns_deterministic_receipt(tmp_path):
    store = JsonSolanaSlotCursorStore(tmp_path / "cursor.json")
    observation = _observation(10, "sig")
    first = advance_and_persist_solana_cursor(store, observation)
    second = advance_and_persist_solana_cursor(
        JsonSolanaSlotCursorStore(tmp_path / "cursor.json"),
        observation,
    )
    assert first.advanced is True
    assert first.current_cursor_id == second.current_cursor_id
    assert store.load().slot == 10


def test_advance_rejects_regression(tmp_path):
    store = JsonSolanaSlotCursorStore(tmp_path / "cursor.json")
    advance_and_persist_solana_cursor(store, _observation(10, "sig"))
    with pytest.raises(ValueError, match="cannot regress"):
        advance_and_persist_solana_cursor(store, _observation(9, "older"))


def test_advance_replay_verifier_matches_receipt(tmp_path):
    store = JsonSolanaSlotCursorStore(tmp_path / "cursor.json")
    observation = _observation(10, "sig")
    receipt = advance_and_persist_solana_cursor(store, observation)
    replay = verify_solana_cursor_advance_replay(store, observation, receipt)
    assert replay.matches is True
    assert replay.original_receipt_id == receipt.receipt_id


def test_advance_replay_verifier_rejects_drift(tmp_path):
    store = JsonSolanaSlotCursorStore(tmp_path / "cursor.json")
    observation = _observation(10, "sig")
    receipt = advance_and_persist_solana_cursor(store, observation)
    with pytest.raises(ValueError, match="does not match"):
        verify_solana_cursor_advance_replay(
            store,
            _observation(11, "next"),
            receipt,
        )
