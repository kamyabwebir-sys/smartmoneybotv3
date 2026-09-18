from dataclasses import FrozenInstanceError

import pytest

from smart_money.domain.solana_observation import (
    SolanaChainObservation,
    SolanaCursorSequenceCheckpoint,
    SolanaSlotCursor,
    replay_solana_commitment_transition,
    replay_solana_observation_order,
    validate_solana_commitment_transition,
    validate_solana_observation_order,
)


def _observation(**overrides: object) -> SolanaChainObservation:
    values: dict[str, object] = {
        "slot": 250,
        "observed_at": 1_700_000_000,
        "transaction_signature": "5abc",
        "program_id": "raydium",
        "subject": "solana:mainnet-beta:wallet",
        "facts": {"amount": 10, "accounts": ["a", "b"]},
    }
    values.update(overrides)
    return SolanaChainObservation(**values)


def test_solana_observation_is_canonical_immutable_and_deterministic():
    left = _observation()
    right = _observation(facts={"accounts": ["a", "b"], "amount": 10})
    assert left.observation_id == right.observation_id
    assert left.canonical_dict()["chain"]["namespace"] == "solana"
    assert not hasattr(left, "__dict__")
    with pytest.raises(FrozenInstanceError):
        left.slot = 1  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("slot", -1, "non-negative"),
        ("observed_at", True, "integer"),
        ("transaction_signature", " ", "non-empty"),
        ("commitment", " ", "non-empty"),
    ],
)
def test_solana_observation_fails_closed(field: str, value: object, error: str):
    with pytest.raises((TypeError, ValueError), match=error):
        _observation(**{field: value})


def test_only_solana_mainnet_beta_is_accepted():
    from smart_money.domain.market_identity import ChainId

    with pytest.raises(ValueError, match="mainnet-beta"):
        _observation(chain=ChainId("solana", "devnet"))


def test_ordering_key_is_total_and_monotonic():
    first = _observation(slot=10, observed_at=100, transaction_signature="a")
    second = _observation(slot=11, observed_at=1, transaction_signature="b")
    assert first.ordering_key == (10, 100, "a")
    validate_solana_observation_order(first, second)


def test_slot_cursor_advances_monotonically_and_is_deterministic():
    first = _observation(slot=10, observed_at=100, transaction_signature="a")
    second = _observation(slot=11, observed_at=101, transaction_signature="b")
    cursor = SolanaSlotCursor()
    advanced = cursor.advance(first).advance(second)
    assert advanced == SolanaSlotCursor.from_observation(second)
    assert advanced.canonical_id == SolanaSlotCursor.from_observation(second).canonical_id


def test_slot_cursor_rejects_regression_and_invalid_empty_state():
    with pytest.raises(ValueError, match="cannot regress"):
        SolanaSlotCursor.from_observation(
            _observation(slot=10, observed_at=100, transaction_signature="a")
        ).advance(_observation(slot=9, observed_at=101, transaction_signature="b"))
    with pytest.raises(ValueError, match="empty cursor"):
        SolanaSlotCursor(transaction_signature="sig")


def test_ordering_regression_and_collision_fail_closed():
    first = _observation(slot=10, observed_at=100, transaction_signature="a")
    with pytest.raises(ValueError, match="regressed"):
        validate_solana_observation_order(
            first,
            _observation(slot=9, observed_at=999, transaction_signature="z"),
        )
    with pytest.raises(ValueError, match="collision"):
        validate_solana_observation_order(
            first,
            _observation(
                slot=10,
                observed_at=100,
                transaction_signature="a",
                facts={"x": 1},
            ),
        )


def test_commitment_transition_allows_only_monotonic_upgrade():
    processed = _observation(commitment="processed")
    confirmed = _observation(commitment="confirmed")
    finalized = _observation(commitment="finalized")
    validate_solana_commitment_transition(processed, confirmed)
    validate_solana_commitment_transition(confirmed, finalized)
    with pytest.raises(ValueError, match="regressed"):
        validate_solana_commitment_transition(finalized, confirmed)


def test_commitment_and_identity_validation_fail_closed():
    with pytest.raises(ValueError, match="unsupported"):
        _observation(commitment="unknown")
    with pytest.raises(ValueError, match="same observation"):
        validate_solana_commitment_transition(
            _observation(commitment="processed"),
            _observation(
                commitment="confirmed",
                transaction_signature="different",
            ),
        )


def test_commitment_replay_receipt_is_deterministic():
    receipt = replay_solana_commitment_transition(
        _observation(commitment="processed"),
        _observation(commitment="confirmed"),
    )
    assert receipt.current_commitment == "confirmed"
    assert receipt.transition_id == replay_solana_commitment_transition(
        _observation(commitment="processed"),
        _observation(commitment="confirmed"),
    ).transition_id


def test_ordering_replay_receipt_is_deterministic():
    values = [
        _observation(slot=1, observed_at=10, transaction_signature="a"),
        _observation(slot=2, observed_at=1, transaction_signature="b"),
    ]
    receipt = replay_solana_observation_order(values)
    assert receipt.observation_ids == tuple(item.observation_id for item in values)
    assert receipt.sequence_id == replay_solana_observation_order(tuple(values)).sequence_id


def test_ordering_replay_rejects_regression_and_empty_input():
    with pytest.raises(ValueError, match="non-empty"):
        replay_solana_observation_order([])
    with pytest.raises(ValueError, match="regressed"):
        replay_solana_observation_order(
            [
                _observation(slot=2, observed_at=1, transaction_signature="b"),
                _observation(slot=1, observed_at=1, transaction_signature="a"),
            ]
        )


def test_cursor_sequence_checkpoint_binds_sequence_tail_deterministically():
    values = [
        _observation(slot=1, observed_at=10, transaction_signature="a"),
        _observation(slot=2, observed_at=11, transaction_signature="b"),
    ]
    sequence = replay_solana_observation_order(values)
    cursor = SolanaSlotCursor.from_observation(values[-1])
    checkpoint = SolanaCursorSequenceCheckpoint.from_sequence(sequence, cursor)
    assert checkpoint.observation_count == 2
    assert checkpoint.last_observation_id == values[-1].observation_id
    assert checkpoint.cursor.ordering_key == sequence.last_ordering_key
    assert checkpoint.checkpoint_id == SolanaCursorSequenceCheckpoint.from_sequence(
        sequence, cursor
    ).checkpoint_id


def test_cursor_sequence_checkpoint_rejects_tail_mismatch_and_mutation():
    values = [
        _observation(slot=1, observed_at=10, transaction_signature="a"),
        _observation(slot=2, observed_at=11, transaction_signature="b"),
    ]
    sequence = replay_solana_observation_order(values)
    wrong_cursor = SolanaSlotCursor.from_observation(values[0])
    with pytest.raises(ValueError, match="tail"):
        SolanaCursorSequenceCheckpoint.from_sequence(sequence, wrong_cursor)
    checkpoint = SolanaCursorSequenceCheckpoint.from_sequence(
        sequence, SolanaSlotCursor.from_observation(values[-1])
    )
    with pytest.raises(FrozenInstanceError):
        checkpoint.sequence_id = "tampered"  # type: ignore[misc]
