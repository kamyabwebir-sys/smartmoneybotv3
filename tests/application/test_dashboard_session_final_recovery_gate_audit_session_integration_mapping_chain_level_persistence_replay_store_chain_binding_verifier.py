from __future__ import annotations

from smart_money.adapters.persistence.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store import (  # noqa: E501
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStore,
)
from smart_money.application.dashboard_session_audit_chain import DashboardSessionAuditEntry
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreVerifier,
)
from tests.application.test_dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_verifier import (  # noqa: E501
    _receipt,
)

_Store = (
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStore
)
_StoreVerifier = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreVerifier
)


def _chain_with_audit(store_audit_id: str | None) -> DashboardSessionFinalRecoveryGateAuditChain:
    entries = (
        ()
        if store_audit_id is None
        else (
            DashboardSessionAuditEntry(
                "persistence_replay_store_audit",
                store_audit_id,
                None,
            ),
        )
    )
    from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
        _chain_hash,
    )

    return DashboardSessionFinalRecoveryGateAuditChain(
        entries=entries,
        chain_hash=_chain_hash(entries),
    )

def _store_audit(tmp_path):
    replay = _receipt()
    store = _Store(tmp_path / "replay.json")
    store.append(replay)
    return _StoreVerifier(receipt_store=store).verify(replay)


def test_chain_binding_matches_when_store_audit_entry_exists(tmp_path) -> None:
    store_audit = _store_audit(tmp_path)
    chain = _chain_with_audit(store_audit.audit_id)
    result = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier().verify(
            chain=chain,
            store_audit=store_audit,
        )
    )
    assert result.matches is True
    assert result.chain_entry_present is True


def test_chain_binding_fails_closed_when_entry_is_missing(tmp_path) -> None:
    store_audit = _store_audit(tmp_path)
    chain = _chain_with_audit(None)
    result = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier().verify(
            chain=chain,
            store_audit=store_audit,
        )
    )
    assert result.matches is False
    assert "persistence_replay_store_audit_missing_in_chain" in result.mismatches
