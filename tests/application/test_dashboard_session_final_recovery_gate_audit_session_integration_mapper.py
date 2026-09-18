from __future__ import annotations

from dataclasses import dataclass

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
    dashboard_session_final_recovery_gate_audit_session_integration_mapper as igm_model,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
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
        chain_replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayVerifier()
        .verify(chain, chain)
    )
    recovery = (
        recovery_gate_model.DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
            chain, chain_replay, chain_replay
        )
    )
    recovery_replay = (
        recovery_replay_model.DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier()
        .verify(recovery, chain, chain_replay, chain_replay)
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
        chain, full_audit, None
    )
    return chain, full_audit, binding


def test_integration_mapper_ready() -> None:
    chain, full_audit, binding = _inputs()
    mapper = igm_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper()

    result = mapper.map(chain, full_audit, binding)

    assert result.decision == "READY"
    assert result.chain_id == chain.chain_id
    assert result.chain_hash == chain.chain_hash
    assert result.full_audit_receipt_id == full_audit.full_audit_id
    assert result.binding_receipt_id == binding.receipt_id
    assert result.chain_entry_count == len(chain.entries)
    assert result.previous_integration_session_id is None
    assert result.mapping_id


def test_integration_mapper_blocked_on_full_audit_mismatch() -> None:
    chain, full_audit, binding = _inputs()
    altered = full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt(
        expected_chain_id="different",
        expected_chain_hash=full_audit.expected_chain_hash,
        recovery_gate_chain_id=full_audit.recovery_gate_chain_id,
        chain_replay_verification_id=full_audit.chain_replay_verification_id,
        persisted_chain_replay_verification_id=(
            full_audit.persisted_chain_replay_verification_id
        ),
        recovery_replay_verification_id=full_audit.recovery_replay_verification_id,
        persisted_recovery_replay_verification_id=(
            full_audit.persisted_recovery_replay_verification_id
        ),
        matches=False,
        mismatches=("chain_id",),
    )
    mapper = igm_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper()
    result = mapper.map(chain, altered, binding)

    assert result.decision == "BLOCKED"
    assert result.reason_code == "CHAIN_MISMATCH"


def test_integration_mapper_links_previous_mapping_chain_id() -> None:
    chain, full_audit, binding = _inputs()
    mapper = igm_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper()
    first = mapper.map(chain, full_audit, binding)
    second = mapper.map(chain, full_audit, binding, previous_mapping=first)

    assert second.decision == "READY"
    assert second.previous_integration_session_id == first.mapping_id
    assert first.mapping_id != second.mapping_id
