import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.adapters.persistence.token_safety_candidate_report_store import (
    JsonTokenSafetyCandidateEvidenceReportStore,
)
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.solana_candidate_ledger_projection import ingest_solana_candidate
from smart_money.application.token_safety_candidate_binding import bind_token_safety_to_candidate
from smart_money.application.token_safety_candidate_binding_ledger import (
    ingest_token_safety_candidate_binding,
)
from smart_money.application.token_safety_candidate_read_model import (
    build_token_safety_candidate_read_model,
)
from smart_money.application.token_safety_candidate_report import (
    build_token_safety_candidate_evidence_report,
)
from smart_money.application.token_safety_candidate_report_store_replay import (
    replay_verify_token_safety_candidate_report_store,
)
from smart_money.application.token_safety_parser import parse_token_safety_observation
from smart_money.core.ids import deterministic_id


def _report(ledger):
    identity = {
        "activity_count": 1, "buy_count": 1, "first_slot": 4, "last_slot": 4,
        "mint": "TOKEN", "reasons": ("buy_count=1",),
        "schema_version": "solana_wallet_token_candidate.v1", "wallet": "W",
    }
    candidate = SolanaWalletTokenCandidate(
        "W", "TOKEN", 1, 1, 4, 4, ("buy_count=1",),
        deterministic_id("solana_wallet_token_candidate", identity),
    )
    observation = parse_token_safety_observation({
        "token": "TOKEN", "observed_at": 10, "mint_authority": None,
        "freeze_authority": None, "update_authority": "U",
        "liquidity_amount": 1000, "holder_concentration_bps": 1200, "deployer": "D",
    })
    ingest_solana_candidate(candidate, ledger)
    ingest_token_safety_candidate_binding(
        bind_token_safety_to_candidate(candidate, observation), ledger
    )
    return build_token_safety_candidate_evidence_report(
        build_token_safety_candidate_read_model(ledger).rows[0]
    )


def test_report_store_replay_matches(tmp_path):
    ledger = EvidenceGroundingLedger()
    report = _report(ledger)
    store = JsonTokenSafetyCandidateEvidenceReportStore(tmp_path / "report.json")
    store.save(report)
    receipt = replay_verify_token_safety_candidate_report_store(store, report, ledger)
    assert receipt.matches is True
    assert receipt.report_id == report.report_id


def test_report_store_replay_fails_when_missing(tmp_path):
    ledger = EvidenceGroundingLedger()
    report = _report(ledger)
    store = JsonTokenSafetyCandidateEvidenceReportStore(tmp_path / "missing.json")
    with pytest.raises(ValueError, match="missing"):
        replay_verify_token_safety_candidate_report_store(store, report, ledger)
