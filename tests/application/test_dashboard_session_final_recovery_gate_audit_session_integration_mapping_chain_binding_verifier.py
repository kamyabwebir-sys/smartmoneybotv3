from __future__ import annotations

from dataclasses import dataclass

from smart_money.adapters.persistence import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_store as replay_store_model,
)
from smart_money.adapters.persistence import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapping_store as mapping_store_model,
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
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_binding_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_persistence_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier,
)


@dataclass(frozen=True, slots=True)
class _ChainLike:
    chain_id: str
    chain_hash: str
    entries: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class _ToyStore:
    mapping: dict[str, object]

    def get(self, verification_id: str) -> object | None:
        return self.mapping.get(verification_id)


def _mapping_pair() -> tuple[
    object,
    mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
    object,
]:
    chain = DashboardSessionFinalRecoveryGateAuditChain(entries=(), chain_hash="0" * 64)
    chain_replay = chain_replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayVerifier().verify(
        chain, chain
    )
    recovery_gate = recovery_gate_model.DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
        chain, chain_replay, chain_replay
    )
    recovery_replay = recovery_replay_model.DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier().verify(
        recovery_gate,
        chain,
        chain_replay,
        chain_replay,
    )
    full_audit = full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier(
        chain_replay_store=_ToyStore({chain_replay.verification_id: chain_replay}),
        recovery_replay_store=_ToyStore(
            {recovery_replay.verification_id: recovery_replay},
        ),
    ).verify(chain, chain_replay, recovery_gate, recovery_replay)
    binding = binding_model.DashboardSessionFinalRecoveryGateAuditFullAuditBinder().bind(
        chain, full_audit, None
    )
    mapping = mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper().map(
        chain, full_audit, binding
    )
    mapping_replay = DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier().verify(
        mapping,
        mapping,
    )
    return chain, mapping, mapping_replay


def test_integration_mapping_chain_binding_verifier_round_trip(tmp_path) -> None:
    chain, mapping, mapping_replay = _mapping_pair()
    mapping_store = mapping_store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore(
        tmp_path / "mapping-store.json"
    )
    replay_store = replay_store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayStore(
        tmp_path / "mapping-replay-store.json"
    )
    mapping_store.append(mapping)
    replay_store.append(mapping_replay)

    verifier = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingVerifier(
            chain_persistence_verifier=(
                DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier(
                    mapping_store=mapping_store,
                    replay_store=replay_store,
                )
            ),
            replay_persistence_verifier=(
                DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier(
                    receipt_store=replay_store
                )
            ),
        )
    )

    receipt = verifier.verify(chain=chain, mapping=mapping, mapping_replay=mapping_replay)

    assert receipt.chain_matches is True
    assert receipt.persisted_chain_persistence_verification is True
    assert receipt.persisted_mapping_replay_persistence_verification is True
    assert receipt.mismatches == ()


def test_integration_mapping_chain_binding_verifier_rejects_chain_mismatch(tmp_path) -> None:
    chain, mapping, mapping_replay = _mapping_pair()
    mismatched_chain = _ChainLike(
        chain_id="different-chain-id",
        chain_hash="1" * 64,
        entries=chain.entries,
    )

    mapping_store = mapping_store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore(
        tmp_path / "mapping-store.json"
    )
    replay_store = replay_store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayStore(
        tmp_path / "mapping-replay-store.json"
    )
    mapping_store.append(mapping)
    replay_store.append(mapping_replay)

    verifier = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingVerifier(
            chain_persistence_verifier=(
                DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier(
                    mapping_store=mapping_store,
                    replay_store=replay_store,
                )
            ),
            replay_persistence_verifier=(
                DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier(
                    receipt_store=replay_store
                )
            ),
        )
    )

    receipt = verifier.verify(
        chain=mismatched_chain,
        mapping=mapping,
        mapping_replay=mapping_replay,
    )

    assert receipt.chain_matches is False
    assert "integration_mapping_chain_link_mismatch" in receipt.mismatches
    assert "chain_id_mismatch" in receipt.mismatches


def test_integration_mapping_chain_binding_verifier_uses_persistence_receipts(tmp_path) -> None:
    chain, mapping, mapping_replay = _mapping_pair()
    mapping_store = mapping_store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore(
        tmp_path / "mapping-store.json"
    )
    replay_store = replay_store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayStore(
        tmp_path / "mapping-replay-store.json"
    )
    replay_store.append(mapping_replay)

    verifier = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingVerifier(
            chain_persistence_verifier=(
                DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier(
                    mapping_store=mapping_store,
                    replay_store=replay_store,
                )
            ),
            replay_persistence_verifier=(
                DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier(
                    receipt_store=replay_store
                )
            ),
        )
    )

    receipt = verifier.verify(chain=chain, mapping=mapping, mapping_replay=mapping_replay)

    assert receipt.chain_matches is False
    assert "persisted_session_integration_mapping_missing" in receipt.mismatches
    assert "persisted_mapping_replay_verification" not in "".join(receipt.mismatches)
    assert receipt.persisted_mapping_replay_persistence_verification is True
