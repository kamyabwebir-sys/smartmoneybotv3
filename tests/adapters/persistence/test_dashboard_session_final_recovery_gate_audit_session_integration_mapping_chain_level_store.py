from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_store import (  # noqa: E501
    JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore,
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


def test_chain_level_store_is_idempotent_and_reloads(tmp_path) -> None:
    path = tmp_path / "chain-level.json"
    receipt = _receipt()
    store = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore(path)

    assert store.append(receipt) == receipt.audit_id
    assert store.append(receipt) == receipt.audit_id
    assert store.receipt_count == 1

    reloaded = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore(
        path
    )
    assert reloaded.get(receipt.audit_id) == receipt
    assert reloaded.content_hash == store.content_hash


def test_chain_level_store_recovers_temporary_file(tmp_path) -> None:
    path = tmp_path / "chain-level.json"
    receipt = _receipt()
    store = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore(path)
    store.append(receipt)

    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.unlink()

    recovered = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore(
        path
    )
    assert recovered.get(receipt.audit_id) == receipt
    assert path.is_file()


def test_chain_level_store_rejects_corruption(tmp_path) -> None:
    path = tmp_path / "chain-level.json"
    store = JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore(path)
    store.append(_receipt())
    document = json.loads(path.read_text(encoding="utf-8"))
    document["receipts"][0]["matches"] = False
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelStore(path)
