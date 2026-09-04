from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from smart_money.adapters.persistence import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_store as store_model,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_recovery_full_audit_verifier as full_audit_model,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_recovery_gate as recovery_gate_model,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_recovery_replay_verifier as recovery_replay_model,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapper as mapping_model,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier as mapping_replay_verifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditChainReplayVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_full_audit_binding import (
    DashboardSessionFinalRecoveryGateAuditFullAuditBinder,
)


def _inputs():
    chain = DashboardSessionFinalRecoveryGateAuditChain(
        entries=(),
        chain_hash="0" * 64,
    )
    chain_replay = DashboardSessionFinalRecoveryGateAuditChainReplayVerifier().verify(
        chain, chain
    )
    recovery = recovery_gate_model.DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
        chain,
        chain_replay,
        chain_replay,
    )
    recovery_replay = (
        recovery_replay_model.DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier().verify(
            recovery,
            chain,
            chain_replay,
            chain_replay,
        )
    )
    full_audit = (
        full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier(
            chain_replay_store=_ToyStore({chain_replay.verification_id: chain_replay}),
            recovery_replay_store=_ToyStore(
                {recovery_replay.verification_id: recovery_replay},
            ),
        ).verify(chain, chain_replay, recovery, recovery_replay)
    )
    binding = DashboardSessionFinalRecoveryGateAuditFullAuditBinder().bind(
        chain,
        full_audit,
    )
    mapping = mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper().map(
        chain,
        full_audit,
        binding,
    )
    replay = (
        mapping_replay_verifier.DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier().verify(
            mapping,
            mapping,
        )
    )
    return chain_replay, replay


@dataclass(frozen=True, slots=True)
class _ToyStore:
    mapping: dict[str, object]

    def get(self, verification_id: str) -> object | None:
        return self.mapping.get(verification_id)


def test_mapping_replay_store_is_round_trip_and_idempotent(tmp_path) -> None:
    _, replay = _inputs()
    path = tmp_path / "mapping_replay_store.json"
    store = store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayStore(path)

    assert store.append(replay) == replay.verification_id
    assert store.append(replay) == replay.verification_id

    restored = store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayStore(
        path
    )
    assert restored.receipt_count == 1
    assert restored.get(replay.verification_id) == replay
    assert list(restored.iter_receipts()) == [replay]


def test_mapping_replay_store_rejects_hash_corruption(tmp_path) -> None:
    _, replay = _inputs()
    path = tmp_path / "mapping_replay_store.json"
    store = store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayStore(
        path
    )
    store.append(replay)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["content_hash"] = "f" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayStore(path)
