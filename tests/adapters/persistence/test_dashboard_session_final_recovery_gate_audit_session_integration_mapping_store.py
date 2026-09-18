import json
from dataclasses import dataclass, replace

import pytest

from smart_money.adapters.persistence import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapping_store as store_model,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_chain_replay_verifier as chain_replay_model,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_full_audit_binding as binding_model,
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
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier,
)

_MappingReplayVerifier = (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier
)


@dataclass(frozen=True, slots=True)
class _ToyStore:
    mapping: dict[str, object]

    def get(self, verification_id: str) -> object | None:
        return self.mapping.get(verification_id)


def _inputs():
    chain = DashboardSessionFinalRecoveryGateAuditChain(
        entries=(),
        chain_hash="0" * 64,
    )
    chain_replay = (
        chain_replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayVerifier().verify(
            chain,
            chain,
        )
    )
    recovery = (
        recovery_gate_model.DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
            chain, chain_replay, chain_replay
        )
    )
    recovery_replay = (
        recovery_replay_model.DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier().verify(
            recovery, chain, chain_replay, chain_replay
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
    binding = binding_model.DashboardSessionFinalRecoveryGateAuditFullAuditBinder().bind(
        chain,
        full_audit,
        None,
    )
    mapping = mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper().map(
        chain,
        full_audit,
        binding,
    )
    return (chain, chain_replay, recovery_replay, binding, mapping)


def test_mapping_store_roundtrip_and_idempotence(tmp_path) -> None:
    _, _, _, _, mapping = _inputs()
    path = tmp_path / "integration-mapping-store.json"
    store = store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore(
        path
    )

    assert store.append(mapping) == mapping.mapping_id
    assert store.append(mapping) == mapping.mapping_id
    restored = (
        store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore(
            path
        )
    )

    assert restored.mapping_count == 1
    assert restored.get(mapping.mapping_id) == mapping
    assert list(restored.iter_mappings()) == [mapping]


def test_mapping_store_hash_corruption_is_rejected(tmp_path) -> None:
    _, _, _, _, mapping = _inputs()
    path = tmp_path / "integration-mapping-store.json"
    store = store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore(
        path
    )
    store.append(mapping)
    document = path.read_text(encoding="utf-8")
    payload = json.loads(document)
    payload["content_hash"] = "f" * 64
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore(path)


def test_integration_mapping_replay_verifier_detects_mismatch() -> None:
    _, _, _, _, expected = _inputs()
    verifier = _MappingReplayVerifier()
    actual = replace(
        expected,
        chain_replay_verification_id="1" * 64,
    )

    receipt = verifier.verify(expected, actual)

    assert receipt.matches is False
    assert "chain_replay_verification_id" in receipt.mismatches
    assert receipt.actual_mapping_id != receipt.expected_mapping_id
    assert receipt.verification_id


def test_integration_mapping_replay_verifier_matches_identity() -> None:
    _, _, _, _, expected = _inputs()
    verifier = _MappingReplayVerifier()
    actual = replace(expected)

    receipt = verifier.verify(expected, actual)

    assert receipt.matches is True
    assert receipt.mismatches == ()
    assert receipt.expected_mapping_id == receipt.actual_mapping_id
