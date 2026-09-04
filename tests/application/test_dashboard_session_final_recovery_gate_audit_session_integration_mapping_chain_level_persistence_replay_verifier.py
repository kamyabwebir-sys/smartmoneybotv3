from __future__ import annotations

import pytest

from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceAuditReceipt,
)

_AuditReceipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceAuditReceipt
)  # noqa: E501


def _audit(  # noqa: E501
    matches: bool = True,
) -> _AuditReceipt:
    return _AuditReceipt(
        expected_audit_id="expected-chain-level-audit",
        persisted_audit_id="persisted-chain-level-audit",
        matches=matches,
        mismatches=() if matches else ("persisted_chain_level_audit_receipt_mismatch",),
    )


def test_chain_level_persistence_replay_matches_identical_receipts() -> None:
    audit = _audit()
    result = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayVerifier().verify(
            expected=audit,
            actual=audit,
        )
    )
    assert result.matches is True
    assert result.mismatches == ()
    assert result.expected_persistence_audit_id == audit.audit_id
    assert result.actual_persistence_audit_id == audit.audit_id


def test_chain_level_persistence_replay_fails_on_receipt_mismatch() -> None:
    expected = _audit()
    actual = _audit(matches=False)
    result = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayVerifier().verify(
            expected=expected,
            actual=actual,
        )
    )
    assert result.matches is False
    assert result.mismatches == ("persistence_audit_id_mismatch",)


def test_chain_level_persistence_replay_rejects_wrong_type() -> None:
    with pytest.raises(TypeError, match="expected must be"):
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayVerifier().verify(
            expected=object(),
            actual=_audit(),
        )
