import pytest

from smart_money.application.solana_observation_ledger_projection import (
    ingest_solana_observation,
    verify_solana_observation_replay,
)
from smart_money.domain.solana_observation import SolanaChainObservation
from smart_money.ingestion.ledger import EvidenceGroundingLedger


def _observation():
    return SolanaChainObservation(
        slot=250,
        observed_at=1_700_000_000,
        transaction_signature="5abc",
        program_id="raydium",
        subject="solana:mainnet-beta:wallet",
        facts={"amount": 10},
    )


def test_projection_appends_and_is_idempotent():
    ledger = EvidenceGroundingLedger()
    observation = _observation()
    first = ingest_solana_observation(observation, ledger)
    second = ingest_solana_observation(observation, ledger)
    assert first.observation_id == observation.observation_id
    assert first.evidence_id == second.evidence_id
    assert first.already_present is False
    assert second.already_present is True
    assert ledger.entry_count == 1
    assert ledger.get(first.evidence_id) is not None


def test_projection_receipt_is_deterministic():
    left = ingest_solana_observation(_observation(), EvidenceGroundingLedger())
    right = ingest_solana_observation(_observation(), EvidenceGroundingLedger())
    assert left.canonical_dict() == right.canonical_dict()


def test_projection_rejects_wrong_input():
    with pytest.raises(TypeError, match="SolanaChainObservation"):
        ingest_solana_observation(object(), EvidenceGroundingLedger())  # type: ignore[arg-type]


def test_replay_verifier_matches_persisted_payload():
    ledger = EvidenceGroundingLedger()
    observation = _observation()
    ingest_solana_observation(observation, ledger)
    receipt = verify_solana_observation_replay(observation, ledger)
    assert receipt.observation_id == observation.observation_id
    assert receipt.evidence_id == ledger.get(receipt.evidence_id).get_canonical_id()


def test_replay_verifier_fails_when_missing():
    with pytest.raises(ValueError, match="missing"):
        verify_solana_observation_replay(_observation(), EvidenceGroundingLedger())
