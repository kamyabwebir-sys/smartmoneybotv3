from __future__ import annotations

from dataclasses import dataclass

from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditChainReplayVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_full_audit_binding import (
    DashboardSessionFinalRecoveryGateAuditFullAuditBinder,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_full_audit_verifier import (
    DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_gate import (
    DashboardSessionFinalRecoveryGateAuditRecoveryGate,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapper import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_persistence_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt,
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier,
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
    chain_replay = DashboardSessionFinalRecoveryGateAuditChainReplayVerifier().verify(
        chain, chain
    )
    recovery = DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
        chain, chain_replay, chain_replay
    )
    recovery_replay = DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier().verify(
        recovery, chain, chain_replay, chain_replay
    )
    full_audit = DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier(
        chain_replay_store=_ToyStore({chain_replay.verification_id: chain_replay}),
        recovery_replay_store=_ToyStore(
            {recovery_replay.verification_id: recovery_replay},
        ),
    ).verify(chain, chain_replay, recovery, recovery_replay)
    binding = DashboardSessionFinalRecoveryGateAuditFullAuditBinder().bind(chain, full_audit)
    mapping = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper().map(
        chain,
        full_audit,
        binding,
    )
    mapping_replay = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier().verify(
            mapping,
            mapping,
        )
    )
    return chain_replay, mapping_replay


def test_mapping_replay_persistence_round_trip() -> None:
    chain_replay, mapping_replay = _inputs()
    store = _ToyStore({mapping_replay.verification_id: mapping_replay})
    result = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier(
            receipt_store=store
        ).verify(mapping_replay)
    )

    assert result.matches is True
    assert result.persisted_verification_id == mapping_replay.verification_id
    assert result.expected_verification_id == mapping_replay.verification_id
    assert result.mismatches == ()


def test_mapping_replay_persistence_reports_missing() -> None:
    chain_replay, mapping_replay = _inputs()
    store = _ToyStore({})
    result = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier(
            receipt_store=store
        ).verify(mapping_replay)
    )

    assert result.matches is False
    assert result.persisted_verification_id is None
    assert result.mismatches == ("persisted_replay_receipt_missing",)


def test_mapping_replay_persistence_reports_mismatch() -> None:
    chain_replay, mapping_replay = _inputs()
    mutated = mapping_replay.__class__(
        expected_mapping_id=mapping_replay.expected_mapping_id,
        actual_mapping_id="x" * 64,
        expected_full_audit_receipt_id=mapping_replay.expected_full_audit_receipt_id,
        actual_full_audit_receipt_id=mapping_replay.actual_full_audit_receipt_id,
        expected_full_audit_verification_id=mapping_replay.expected_full_audit_verification_id,
        actual_full_audit_verification_id=mapping_replay.actual_full_audit_verification_id,
        expected_binding_receipt_id=mapping_replay.expected_binding_receipt_id,
        actual_binding_receipt_id=mapping_replay.actual_binding_receipt_id,
        expected_chain_replay_verification_id=mapping_replay.expected_chain_replay_verification_id,
        actual_chain_replay_verification_id=mapping_replay.actual_chain_replay_verification_id,
        matches=False,
        mismatches=("actual_mapping_id",),
    )
    store = _ToyStore({mapping_replay.verification_id: mapping_replay})
    result = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier(
            receipt_store=store
        ).verify(mutated)
    )

    assert result.matches is False
    assert result.persisted_verification_id == mapping_replay.verification_id
    assert result.mismatches == ("persisted_replay_receipt_mismatch",)


def test_mapping_replay_persistence_audit_is_deterministic() -> None:
    _, mapping_replay = _inputs()
    first = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt(
        expected_verification_id=mapping_replay.verification_id,
        persisted_verification_id=mapping_replay.verification_id,
        matches=True,
    )
    second = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceAuditReceipt(
        expected_verification_id=mapping_replay.verification_id,
        persisted_verification_id=mapping_replay.verification_id,
        matches=True,
    )

    assert first == second
    assert first.audit_id == second.audit_id

