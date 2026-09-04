from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store import (  # noqa: E501
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStore,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayReceipt,
)

_Receipt = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayReceipt
)


def _receipt() -> _Receipt:
    return _Receipt(
        expected_persistence_audit_id="expected-audit",
        actual_persistence_audit_id="actual-audit",
        matches=True,
    )


def test_replay_store_is_idempotent_and_reloads(tmp_path) -> None:
    path = tmp_path / "replay.json"
    receipt = _receipt()
    store = (
        JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStore(
            path
        )
    )
    assert store.append(receipt) == receipt.verification_id
    assert store.append(receipt) == receipt.verification_id
    reloaded = (
        JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStore(
            path
        )
    )
    assert reloaded.get(receipt.verification_id) == receipt
    assert reloaded.content_hash == store.content_hash


def test_replay_store_recovers_temporary_file(tmp_path) -> None:
    path = tmp_path / "replay.json"
    receipt = _receipt()
    store = (
        JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStore(
            path
        )
    )
    store.append(receipt)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.unlink()
    recovered = (
        JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStore(
            path
        )
    )
    assert recovered.get(receipt.verification_id) == receipt
    assert path.is_file()


def test_replay_store_rejects_corruption(tmp_path) -> None:
    path = tmp_path / "replay.json"
    store = (
        JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStore(
            path
        )
    )
    store.append(_receipt())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["receipts"][0]["matches"] = False
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="content hash mismatch"):
        JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelPersistenceReplayStore(path)
