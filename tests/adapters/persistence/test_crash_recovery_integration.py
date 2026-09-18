from __future__ import annotations

# ruff: noqa: E501
import json

import pytest

from smart_money.adapters.persistence.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_replay_store import (
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayStore,
)
from smart_money.adapters.persistence.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_store import (
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceStore,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayAuditReceipt,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceAuditReceipt,
)


def test_json_stores_recover_tmp_with_hash_count_and_receipt_parity(tmp_path) -> None:
    persistence_receipt = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceAuditReceipt(
        expected_audit_id="binding",
        persisted_audit_id="binding",
        matches=True,
    )
    replay_receipt = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayAuditReceipt(
        expected_audit_id="binding",
        generated_audit_id=persistence_receipt.audit_id,
        persisted_audit_id=persistence_receipt.audit_id,
        matches=True,
    )
    for store_type, receipt, filename in (
        (
            JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceStore,
            persistence_receipt,
            "persistence.json",
        ),
        (
            JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayStore,
            replay_receipt,
            "replay.json",
        ),
    ):
        path = tmp_path / filename
        store = store_type(path)
        store.append(receipt)
        baseline_hash = store.content_hash
        temporary = path.with_name(f"{path.name}.tmp")
        temporary.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        path.unlink()
        restored = store_type(path)
        assert restored.get(receipt.audit_id) == receipt
        assert restored.receipt_count == 1
        assert restored.content_hash == baseline_hash
        assert not temporary.exists()


def test_recovery_rejects_tampered_tmp_before_replace(tmp_path) -> None:
    path = tmp_path / "replay.json"
    store = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayStore(
        path
    )
    receipt = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayAuditReceipt(
        expected_audit_id="binding",
        generated_audit_id="generated",
        persisted_audit_id="persisted",
        matches=True,
    )
    store.append(receipt)
    temporary = path.with_name(f"{path.name}.tmp")
    document = json.loads(path.read_text(encoding="utf-8"))
    document["receipts"][0]["matches"] = False
    temporary.write_text(json.dumps(document), encoding="utf-8")
    path.unlink()
    with pytest.raises(ValueError, match="content hash mismatch"):
        type(store)(path)
