from __future__ import annotations

import hashlib

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_chain_replay_verifier as replay_verifier,
)
from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditEntry,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.core.serialization import canonical_json


def _chain() -> DashboardSessionFinalRecoveryGateAuditChain:
    return DashboardSessionFinalRecoveryGateAuditChain(
        entries=(),
        chain_hash="0" * 64,
    )


def test_replay_matches() -> None:
    chain = _chain()

    result = replay_verifier.DashboardSessionFinalRecoveryGateAuditChainReplayVerifier().verify(
        chain, chain
    )

    assert result.matches is True
    assert result.mismatches == ()
    assert result.expected_chain_id == result.actual_chain_id
    assert result.verification_id


def test_replay_reports_difference() -> None:
    expected = _chain()
    entry = DashboardSessionAuditEntry("gate", "gate-1", None)
    chain_hash = hashlib.sha256(
        canonical_json(
            {
                "previous_hash": "0" * 64,
                "entry": entry.canonical_dict(),
            }
        ).encode("utf-8")
    ).hexdigest()
    actual = DashboardSessionFinalRecoveryGateAuditChain(
        entries=(entry,),
        chain_hash=chain_hash,
    )

    result = replay_verifier.DashboardSessionFinalRecoveryGateAuditChainReplayVerifier().verify(
        expected, actual
    )

    assert result.matches is False
    assert "chain_id" in result.mismatches
    assert "chain_hash" in result.mismatches
    assert "entry_count" in result.mismatches
