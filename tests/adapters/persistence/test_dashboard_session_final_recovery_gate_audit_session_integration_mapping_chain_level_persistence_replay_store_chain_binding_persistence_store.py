from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_store import (  # noqa: E501
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceStore,
)
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

_Store = (
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceStore
)
_BindingVerifier = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingVerifier
)
_PersistenceVerifier = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceVerifier
)


def _receipt(tmp_path):
    audit = _store_audit(tmp_path)
    chain = _chain_with_audit(audit.audit_id)
    binding = _BindingVerifier().verify(chain=chain, store_audit=audit)

    class Store:
        def get(self, audit_id: str):
            return binding

    return _PersistenceVerifier(receipt_store=Store()).verify(binding)


def test_chain_binding_persistence_store_is_idempotent_and_reloads(tmp_path) -> None:
    receipt = _receipt(tmp_path)
    path = tmp_path / "binding.json"
    store = _Store(path)
    assert store.append(receipt) == receipt.audit_id
    assert store.append(receipt) == receipt.audit_id
    reloaded = _Store(path)
    assert reloaded.get(receipt.audit_id) == receipt
    assert reloaded.content_hash == store.content_hash


def test_chain_binding_persistence_store_recovers_tmp(tmp_path) -> None:
    receipt = _receipt(tmp_path)
    path = tmp_path / "binding.json"
    store = _Store(path)
    store.append(receipt)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.unlink()
    recovered = _Store(path)
    assert recovered.get(receipt.audit_id) == receipt
    assert path.is_file()


def test_chain_binding_persistence_store_rejects_corruption(tmp_path) -> None:
    receipt = _receipt(tmp_path)
    path = tmp_path / "binding.json"
    store = _Store(path)
    store.append(receipt)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["receipts"][0]["matches"] = False
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="content hash mismatch"):
        _Store(path)
