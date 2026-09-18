from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.token_safety_candidate_binding import bind_token_safety_to_candidate
from smart_money.application.token_safety_candidate_binding_ledger import (
    ingest_token_safety_candidate_binding,
)
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.core.ids import deterministic_id


def test_binding_projection_is_idempotent_and_preserves_provenance():
    candidate_identity = {
        "activity_count": 1,
        "buy_count": 1,
        "first_slot": 4,
        "last_slot": 4,
        "mint": "TOKEN",
        "reasons": ("buy_count=1",),
        "schema_version": "solana_wallet_token_candidate.v1",
        "wallet": "W",
    }
    candidate = SolanaWalletTokenCandidate(
        wallet="W",
        mint="TOKEN",
        activity_count=1,
        buy_count=1,
        first_slot=4,
        last_slot=4,
        reasons=("buy_count=1",),
        candidate_id=deterministic_id(
            "solana_wallet_token_candidate", candidate_identity
        ),
    )
    observation = parse_token_safety_observation(
        {
            "token": "TOKEN",
            "observed_at": 10,
            "mint_authority": None,
            "freeze_authority": None,
            "update_authority": "UPDATER",
            "liquidity_amount": 1000,
            "holder_concentration_bps": 1200,
            "deployer": "DEPLOYER",
        }
    )
    binding = bind_token_safety_to_candidate(candidate, observation)
    ledger = EvidenceGroundingLedger()
    first = ingest_token_safety_candidate_binding(binding, ledger)
    second = ingest_token_safety_candidate_binding(binding, ledger)
    payload = ledger.get(first.evidence_id)
    assert first.evidence_id == second.evidence_id
    assert second.already_present is True
    assert payload is not None
    assert payload.metadata["provenance"]["candidate_id"] == candidate.candidate_id
    assert payload.metadata["provenance"]["token_observation_id"] == observation.observation_id
