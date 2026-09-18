from __future__ import annotations

from dataclasses import dataclass

from smart_money.adapters.persistence import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_store as replay_store_model,
)
from smart_money.adapters.persistence import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapping_store as mapping_store_model,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_chain as chain_model,
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
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapper import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt,
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier,
)


@dataclass(frozen=True, slots=True)
class _ToyStore:
    mapping: dict[str, object]

    def get(self, key: str) -> object | None:
        return self.mapping.get(key)


def _mapping_pair():
    chain = chain_model.DashboardSessionFinalRecoveryGateAuditChain(
        entries=(),
        chain_hash="0" * 64,
    )
    chain_replay = chain_replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayVerifier().verify(
        chain,
        chain,
    )
    recovery = recovery_gate_model.DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
        chain, chain_replay, chain_replay
    )
    recovery_replay = recovery_replay_model.DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier().verify(
        recovery, chain, chain_replay, chain_replay
    )
    full_audit = full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier(
        chain_replay_store=_ToyStore({chain_replay.verification_id: chain_replay}),
        recovery_replay_store=_ToyStore(
            {recovery_replay.verification_id: recovery_replay},
        ),
    ).verify(chain, chain_replay, recovery, recovery_replay)
    binding = binding_model.DashboardSessionFinalRecoveryGateAuditFullAuditBinder().bind(
        chain,
        full_audit,
        None,
    )
    mapping = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper().map(
        chain,
        full_audit,
        binding,
    )
    mapping_replay = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier().verify(
        mapping,
        mapping,
    )
    return mapping, mapping_replay


def test_chain_mapping_and_replay_chain_persistence_verifier_round_trip(tmp_path) -> None:
    mapping, mapping_replay = _mapping_pair()
    mapping_store = mapping_store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore(
        tmp_path / "mapping.json"
    )
    replay_store = replay_store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayStore(
        tmp_path / "mapping-replay.json"
    )

    mapping_store.append(mapping)
    replay_store.append(mapping_replay)

    receipt = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier(
        mapping_store=mapping_store,
        replay_store=replay_store,
    ).verify(mapping, mapping_replay)

    assert receipt.matches is True
    assert receipt.mapping_matches is True
    assert receipt.replay_matches is True
    assert receipt.mismatch_mapping_replay_link is False
    assert receipt.mismatches == ()
    assert receipt.persisted_mapping_id == mapping.mapping_id
    assert receipt.persisted_replay_verification_id == mapping_replay.verification_id


def test_chain_mapping_store_persistence_verifier_reports_missing_mapping() -> None:
    mapping, mapping_replay = _mapping_pair()
    empty_store = _ToyStore({})
    replay_store = _ToyStore({mapping_replay.verification_id: mapping_replay})

    receipt = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier(
        mapping_store=empty_store,
        replay_store=replay_store,
    ).verify(mapping, mapping_replay)

    assert receipt.matches is False
    assert receipt.mapping_matches is False
    assert receipt.persisted_mapping_id is None
    assert "persisted_session_integration_mapping_missing" in receipt.mismatches


def test_chain_mapping_store_persistence_verifier_reports_mapping_replay_missing() -> None:
    mapping, mapping_replay = _mapping_pair()
    mapping_store = _ToyStore({mapping.mapping_id: mapping})
    replay_store = _ToyStore({})

    receipt = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier(
        mapping_store=mapping_store,
        replay_store=replay_store,
    ).verify(mapping, mapping_replay)

    assert receipt.matches is False
    assert receipt.mapping_matches is True
    assert receipt.replay_matches is False
    assert receipt.persisted_replay_verification_id is None
    assert "persisted_session_integration_mapping_replay_missing" in receipt.mismatches


def test_chain_mapping_chain_persistence_receipt_is_deterministic() -> None:
    mapping, mapping_replay = _mapping_pair()
    receipt_one = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt(
        expected_mapping_id=mapping.mapping_id,
        persisted_mapping_id=mapping.mapping_id,
        mapping_matches=True,
        expected_replay_verification_id=mapping_replay.verification_id,
        persisted_replay_verification_id=mapping_replay.verification_id,
        replay_matches=True,
        mismatch_mapping_replay_link=False,
        mismatches=(),
    )
    receipt_two = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceAuditReceipt(
        expected_mapping_id=mapping.mapping_id,
        persisted_mapping_id=mapping.mapping_id,
        mapping_matches=True,
        expected_replay_verification_id=mapping_replay.verification_id,
        persisted_replay_verification_id=mapping_replay.verification_id,
        replay_matches=True,
        mismatch_mapping_replay_link=False,
        mismatches=(),
    )

    assert receipt_one == receipt_two
    assert receipt_one.audit_id == receipt_two.audit_id


def test_chain_mapping_chain_verifier_reports_replay_link_mismatch() -> None:
    mapping, mapping_replay = _mapping_pair()
    mapping_store = _ToyStore({mapping.mapping_id: mapping})
    replay_store = _ToyStore(
        {mapping_replay.verification_id: mapping_replay},
    )

    broken = mapping.__class__(
        chain_id=mapping.chain_id,
        chain_hash=mapping.chain_hash,
        chain_entry_count=mapping.chain_entry_count,
        chain_replay_verification_id=mapping.chain_replay_verification_id,
        full_audit_receipt_id=mapping.full_audit_receipt_id,
        full_audit_verification_id=mapping.full_audit_verification_id,
        binding_receipt_id=mapping.binding_receipt_id,
        integration_session_id=mapping.integration_session_id,
        previous_integration_session_id=mapping.previous_integration_session_id,
        decision="BLOCKED",
        reason_code=mapping.reason_code,
    )
    receipt = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier(
        mapping_store=mapping_store,
        replay_store=replay_store,
    ).verify(
        mapping=broken,
        mapping_replay=mapping_replay,
    )

    assert receipt.matches is False
    assert receipt.mapping_matches is False
    assert "mapping_replay_link_mismatch" in receipt.mismatches
    assert receipt.mismatch_mapping_replay_link is True
