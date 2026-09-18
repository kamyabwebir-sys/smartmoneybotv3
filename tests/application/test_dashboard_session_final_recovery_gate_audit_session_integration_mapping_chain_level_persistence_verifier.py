from __future__ import annotations

from dataclasses import dataclass

import pytest

from smart_money.adapters.persistence.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_store import (  # noqa: E501
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceVerifier,
)
from tests.application.test_dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_verifier import (  # noqa: E501
    _build_chain,
    _verifier,
)


def _receipt():
    chain, mapping, mapping_replay = _build_chain(include_replay=True)
    return _verifier(chain, mapping, mapping_replay).verify(
        chain=chain,
        mapping=mapping,
        mapping_replay=mapping_replay,
    )


def test_chain_level_persistence_verifier_matches_persisted_receipt(tmp_path) -> None:
    receipt = _receipt()
    store = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore(
        tmp_path / "chain-level.json"
    )
    store.append(receipt)

    audit = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceVerifier(
            receipt_store=store
        ).verify(receipt)
    )

    assert audit.matches is True
    assert audit.expected_audit_id == receipt.audit_id
    assert audit.persisted_audit_id == receipt.audit_id
    assert audit.mismatches == ()


def test_chain_level_persistence_verifier_fails_closed_when_missing(tmp_path) -> None:
    receipt = _receipt()
    store = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore(
        tmp_path / "chain-level.json"
    )

    audit = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceVerifier(
            receipt_store=store
        ).verify(receipt)
    )

    assert audit.matches is False
    assert audit.persisted_audit_id is None
    assert audit.mismatches == ("persisted_chain_level_audit_receipt_missing",)


@dataclass(frozen=True, slots=True)
class _WrongStore:
    receipt: object

    def get(self, audit_id: str) -> object:
        return self.receipt


def test_chain_level_persistence_verifier_rejects_invalid_store_value() -> None:
    with pytest.raises(TypeError, match="invalid chain-level audit receipt"):
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceVerifier(
            receipt_store=_WrongStore(receipt=object())
        ).verify(_receipt())
