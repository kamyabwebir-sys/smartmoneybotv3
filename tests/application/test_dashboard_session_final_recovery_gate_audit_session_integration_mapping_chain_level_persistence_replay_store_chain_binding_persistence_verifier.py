from __future__ import annotations

from dataclasses import dataclass

import pytest

from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier,
)
from tests.application.test_dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_verifier import (  # noqa: E501
    _chain_with_audit,
    _store_audit,
)


def test_chain_binding_persistence_matches(tmp_path) -> None:
    audit = _store_audit(tmp_path)
    chain = _chain_with_audit(audit.audit_id)
    binding = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier().verify(  # noqa: E501
            chain=chain,
            store_audit=audit,
        )
    )

    @dataclass(frozen=True, slots=True)
    class Store:
        value: object

        def get(self, audit_id: str) -> object:
            return self.value

    result = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceVerifier(  # noqa: E501
        receipt_store=Store(binding)
    ).verify(binding)
    assert result.matches is True
    assert result.persisted_audit_id == binding.audit_id
    assert chain.chain_id


def test_chain_binding_persistence_missing_fails_closed(tmp_path) -> None:
    audit = _store_audit(tmp_path)
    chain = _chain_with_audit(audit.audit_id)
    binding = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier().verify(  # noqa: E501
            chain=chain,
            store_audit=audit,
        )
    )

    @dataclass(frozen=True, slots=True)
    class Store:
        def get(self, audit_id: str) -> object | None:
            return None

    result = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceVerifier(  # noqa: E501
        receipt_store=Store()
    ).verify(binding)
    assert result.matches is False
    assert result.mismatches == ("persisted_chain_binding_receipt_missing",)


def test_chain_binding_persistence_rejects_invalid_store_value(tmp_path) -> None:
    audit = _store_audit(tmp_path)
    chain = _chain_with_audit(audit.audit_id)
    binding = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier().verify(  # noqa: E501
            chain=chain,
            store_audit=audit,
        )
    )

    @dataclass(frozen=True, slots=True)
    class Store:
        def get(self, audit_id: str) -> object:
            return object()

    with pytest.raises(TypeError, match="invalid chain binding receipt"):
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceVerifier(  # noqa: E501
            receipt_store=Store()
        ).verify(binding)
