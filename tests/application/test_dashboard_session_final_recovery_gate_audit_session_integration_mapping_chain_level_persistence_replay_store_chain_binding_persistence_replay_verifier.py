from __future__ import annotations

# ruff: noqa: E501
import pytest

from smart_money.adapters.persistence.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_store import (
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceStore,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayVerifier,
)
from tests.adapters.persistence.test_dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_store import (
    _receipt,
)


def test_replay_verifier_matches_persisted_receipt(tmp_path) -> None:
    receipt = _receipt(tmp_path)
    store = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceStore(
        tmp_path / "binding.json"
    )
    store.append(receipt)
    replay = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayVerifier(
        receipt_store=store
    ).verify(_binding_receipt(tmp_path))
    assert replay.matches is True


def test_replay_verifier_fails_closed_when_missing(tmp_path) -> None:
    store = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceStore(
        tmp_path / "binding.json"
    )
    replay = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayVerifier(
        receipt_store=store
    ).verify(_binding_receipt(tmp_path))
    assert replay.matches is False
    assert replay.mismatches == ("persisted_chain_binding_replay_audit_missing",)


def test_replay_verifier_rejects_wrong_subject(tmp_path) -> None:
    receipt = _receipt(tmp_path)
    store = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceStore(
        tmp_path / "binding.json"
    )
    store.append(receipt)
    with pytest.raises(TypeError, match="chain binding receipt"):
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayVerifier(
            receipt_store=store
        ).verify(receipt)


def _binding_receipt(tmp_path):
    from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_verifier import (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier,
    )
    from tests.adapters.persistence.test_dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_store import (
        _chain_with_audit,
    )
    from tests.application.test_dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_verifier import (
        _store_audit,
    )

    audit = _store_audit(tmp_path)
    chain = _chain_with_audit(audit.audit_id)
    return DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier().verify(
        chain=chain,
        store_audit=audit,
    )
