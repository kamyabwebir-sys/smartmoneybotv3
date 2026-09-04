from __future__ import annotations

# ruff: noqa: E501
import json

import pytest

from smart_money.adapters.persistence.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_replay_store import (
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayStore,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayAuditReceipt,
)

_Store = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayStore
_Receipt = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStoreChainBindingPersistenceReplayAuditReceipt


def _receipt() -> _Receipt:
    return _Receipt(
        expected_audit_id="binding_audit",
        generated_audit_id="persistence_audit",
        persisted_audit_id="persistence_audit",
        matches=True,
    )


def test_replay_receipt_store_is_idempotent_and_reloads(tmp_path) -> None:
    receipt = _receipt()
    path = tmp_path / "replay.json"
    store = _Store(path)
    assert store.append(receipt) == receipt.audit_id
    assert store.append(receipt) == receipt.audit_id
    reloaded = _Store(path)
    assert reloaded.get(receipt.audit_id) == receipt
    assert reloaded.receipt_count == 1
    assert reloaded.content_hash == store.content_hash


def test_replay_receipt_store_recovers_tmp(tmp_path) -> None:
    receipt = _receipt()
    path = tmp_path / "replay.json"
    store = _Store(path)
    store.append(receipt)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.unlink()
    recovered = _Store(path)
    assert recovered.get(receipt.audit_id) == receipt
    assert path.is_file()


def test_replay_receipt_store_rejects_corruption(tmp_path) -> None:
    path = tmp_path / "replay.json"
    store = _Store(path)
    store.append(_receipt())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["receipts"][0]["matches"] = False
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="content hash mismatch"):
        _Store(path)
