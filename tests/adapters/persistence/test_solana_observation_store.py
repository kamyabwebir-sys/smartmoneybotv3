import pytest

from smart_money.adapters.persistence.solana_observation_store import (
    JsonSolanaObservationStore,
)
from smart_money.application.solana_observation_parser import SolanaObservationParser
from smart_money.domain.solana_observation import SolanaChainObservation
from smart_money.ingestion.contracts import EvidencePayload


def _payload():
    return SolanaObservationParser.from_observation(
        SolanaChainObservation(
            slot=250,
            observed_at=1_700_000_000,
            transaction_signature="5abc",
            program_id="raydium",
            subject="wallet",
            facts={"amount": 10},
        )
    ).payload


def test_store_round_trips_and_is_idempotent(tmp_path):
    path = tmp_path / "solana.json"
    payload = _payload()
    first = JsonSolanaObservationStore(path)
    identity = first.append(payload)
    assert first.append(payload) == identity
    second = JsonSolanaObservationStore(path)
    assert second.get(identity) == payload
    assert second.content_hash == first.content_hash


def test_store_rejects_non_solana_payload(tmp_path):
    store = JsonSolanaObservationStore(tmp_path / "solana.json")
    with pytest.raises(ValueError, match="evidence_type"):
        store.append(EvidencePayload("x", "generic", 1, {"x": 1}))


def test_store_replay_verifier_matches_persisted_payload(tmp_path):
    path = tmp_path / "solana.json"
    payload = _payload()
    store = JsonSolanaObservationStore(path)
    store.append(payload)
    observation = SolanaObservationParser.from_payload(payload)
    receipt = store.replay(
        SolanaChainObservation(
            slot=250,
            observed_at=1_700_000_000,
            transaction_signature="5abc",
            program_id="raydium",
            subject="wallet",
            facts={"amount": 10},
        )
    )
    assert receipt.matches is True
    assert receipt.observation_id == observation.observation_id


def test_store_replay_verifier_fails_when_missing(tmp_path):
    store = JsonSolanaObservationStore(tmp_path / "solana.json")
    with pytest.raises(ValueError, match="missing"):
        store.replay(
            SolanaChainObservation(
                slot=1,
                observed_at=1,
                transaction_signature="sig",
                program_id="program",
                subject="wallet",
                facts={},
            )
        )
