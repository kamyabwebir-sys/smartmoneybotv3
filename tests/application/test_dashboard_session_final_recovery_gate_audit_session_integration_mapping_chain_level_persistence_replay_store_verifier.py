from __future__ import annotations

from dataclasses import dataclass

import pytest

from smart_money.adapters.persistence.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store import (  # noqa: E501
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStore,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreVerifier,
)
from tests.adapters.persistence.test_dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store import (  # noqa: E501
    _receipt,
)

_Store = (
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStore
)
_Verifier = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreVerifier
)


def test_store_verifier_matches_persisted_receipt(tmp_path) -> None:
    receipt = _receipt()
    store = _Store(tmp_path / "replay.json")
    store.append(receipt)
    audit = _Verifier(receipt_store=store).verify(receipt)
    assert audit.matches is True
    assert audit.persisted_verification_id == receipt.verification_id


def test_store_verifier_fails_closed_when_missing(tmp_path) -> None:
    receipt = _receipt()
    store = _Store(tmp_path / "replay.json")
    audit = _Verifier(receipt_store=store).verify(receipt)
    assert audit.matches is False
    assert audit.mismatches == ("persisted_persistence_replay_receipt_missing",)


@dataclass(frozen=True, slots=True)
class _InvalidStore:
    def get(self, verification_id: str) -> object:
        return object()


def test_store_verifier_rejects_invalid_store_value() -> None:
    with pytest.raises(TypeError, match="invalid persistence replay receipt"):
        _Verifier(receipt_store=_InvalidStore()).verify(_receipt())
