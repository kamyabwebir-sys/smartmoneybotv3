from __future__ import annotations

from dataclasses import dataclass

import pytest

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_chain_replay_verifier as chain_replay_model,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_full_audit_binding as full_audit_binding_model,
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
    dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_persistence_verifier as mapping_replay_persistence_verifier,
)
from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditChain,
)
from smart_money.application.dashboard_session_audit_final_replay_verifier import (
    DashboardSessionAuditFinalReplayVerifier,
)
from smart_money.application.dashboard_session_audit_finalizer import (
    DashboardSessionAuditChainFinalizer,
)
from smart_money.application.dashboard_session_audit_head_anchor import (
    DashboardSessionAuditHeadAnchor,
)
from smart_money.application.dashboard_session_final_audit_chain import (
    DashboardSessionFinalAuditChain,
)
from smart_money.application.dashboard_session_final_audit_chain_replay_verifier import (
    DashboardSessionFinalAuditChainReplayVerifier,
)
from smart_money.application.dashboard_session_final_audit_recovery_gate import (
    DashboardSessionFinalAuditRecoveryGate,
)
from smart_money.application.dashboard_session_final_audit_recovery_replay_verifier import (
    DashboardSessionFinalAuditRecoveryReplayVerifier,
)
from smart_money.application.dashboard_session_final_recovery_audit_chain import (
    DashboardSessionFinalRecoveryAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_audit_chain_replay_verifier import (
    DashboardSessionFinalRecoveryAuditChainReplayVerifier,
)
from smart_money.application.dashboard_session_final_recovery_chain_gate import (
    DashboardSessionFinalRecoveryChainGate,
)
from smart_money.application.dashboard_session_final_recovery_chain_replay_verifier import (
    DashboardSessionFinalRecoveryChainReplayVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier,
)
from smart_money.application.dashboard_session_recovery_gate import (
    DashboardSessionRecoveryGate,
)
from smart_money.application.dashboard_session_recovery_replay_verifier import (
    DashboardSessionRecoveryReplayVerifier,
)


@dataclass(frozen=True, slots=True)
class _ToyStore:
    mapping: dict[str, object]

    def get(self, verification_id: str) -> object | None:
        return self.mapping.get(verification_id)


def _inputs():
    source = DashboardSessionAuditChain(entries=(), chain_hash="0" * 64)
    anchor = DashboardSessionAuditHeadAnchor.from_chain(source)
    recovery = DashboardSessionRecoveryGate().evaluate(source, anchor)
    recovery_replay = DashboardSessionRecoveryReplayVerifier().verify(source, anchor, recovery)
    final = DashboardSessionAuditChainFinalizer().finalize(
        source, anchor, recovery, recovery_replay
    )
    final_replay = DashboardSessionAuditFinalReplayVerifier().verify(
        final, source, anchor, recovery, recovery_replay
    )
    final_chain = DashboardSessionFinalAuditChain.from_chain(source, final, final_replay)
    final_chain_replay = DashboardSessionFinalAuditChainReplayVerifier().verify(
        final_chain, final_chain
    )
    final_recovery = DashboardSessionFinalAuditRecoveryGate().evaluate(
        final_chain, final_chain_replay, final_chain_replay
    )
    final_recovery_replay = DashboardSessionFinalAuditRecoveryReplayVerifier().verify(
        final_recovery,
        final_chain,
        final_chain_replay,
        final_chain_replay,
    )
    recovery_chain = DashboardSessionFinalRecoveryAuditChain.from_chain(
        final_chain, final_recovery, final_recovery_replay
    )
    recovery_chain_replay = DashboardSessionFinalRecoveryAuditChainReplayVerifier().verify(
        recovery_chain, recovery_chain
    )
    gate = DashboardSessionFinalRecoveryChainGate().evaluate(
        recovery_chain, recovery_chain_replay, recovery_chain_replay
    )
    gate_replay = DashboardSessionFinalRecoveryChainReplayVerifier().verify(
        gate, recovery_chain, recovery_chain_replay, recovery_chain_replay
    )
    return recovery_chain, gate, gate_replay


def test_gate_audit_chain_integrates_gate_receipts() -> None:
    chain, gate, replay = _inputs()

    integrated = DashboardSessionFinalRecoveryGateAuditChain.from_chain(chain, gate, replay)

    assert len(integrated.entries) == len(chain.entries) + 2
    assert integrated.entries[-2].entry_kind == "gate"
    assert integrated.entries[-1].entry_kind == "gate_replay"
    assert integrated.entries[-1].parent_id == gate.receipt_id
    assert integrated.chain_id


def test_gate_audit_chain_rejects_non_matching_replay() -> None:
    chain, gate, replay = _inputs()
    mismatch = type(replay)(
        expected_receipt_id=replay.expected_receipt_id,
        actual_receipt_id="different",
        matches=False,
        mismatches=("actual_receipt_id",),
    )

    with pytest.raises(ValueError, match="non-matching gate replay"):
        DashboardSessionFinalRecoveryGateAuditChain.from_chain(chain, gate, mismatch)


def _mapping_inputs():
    source_chain, gate, gate_replay = _inputs()
    final_gate_chain = DashboardSessionFinalRecoveryGateAuditChain.from_chain(
        source_chain, gate, gate_replay
    )
    final_gate_replay = (
        chain_replay_model.DashboardSessionFinalRecoveryGateAuditChainReplayVerifier().verify(
            final_gate_chain, final_gate_chain
        )
    )
    recovery_receipt = (
        recovery_gate_model.DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
            final_gate_chain, final_gate_replay, final_gate_replay
        )
    )
    recovery_replay = (
        recovery_replay_model.DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier().verify(
            recovery_receipt,
            final_gate_chain,
            final_gate_replay,
            final_gate_replay,
        )
    )
    full_audit_receipt = (
        full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier(
            chain_replay_store=_ToyStore(
                {final_gate_replay.verification_id: final_gate_replay},
            ),
            recovery_replay_store=_ToyStore(
                {recovery_replay.verification_id: recovery_replay},
            ),
        ).verify(
            final_gate_chain,
            final_gate_replay,
            recovery_receipt,
            recovery_replay,
        )
    )
    binding_receipt = (
        full_audit_binding_model.DashboardSessionFinalRecoveryGateAuditFullAuditBinder().bind(
            final_gate_chain, full_audit_receipt, None
        )
    )
    mapping = mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationMapper().map(
        final_gate_chain,
        full_audit_receipt,
        binding_receipt,
    )
    mapping_replay = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier()
        .verify(mapping, mapping)
    )
    return source_chain, gate, final_gate_replay, final_gate_chain, mapping, mapping_replay


def test_chain_from_chain_accepts_ready_integration_mapping() -> None:
    source_chain, gate, final_gate_replay, final_gate_chain, mapping, mapping_replay = (
        _mapping_inputs()
    )
    _ = source_chain

    integrated = DashboardSessionFinalRecoveryGateAuditChain.from_chain(
        final_gate_chain,
        integration_mapping=mapping,
        integration_mapping_replay=mapping_replay,
    )

    assert integrated.entries[-4].entry_kind == "gate"
    assert integrated.entries[-3].entry_kind == "gate_replay"
    assert integrated.entries[-2].entry_kind == "integration_mapping"
    assert integrated.entries[-1].entry_kind == "integration_mapping_replay"
    assert integrated.entries[-1].entry_id == mapping_replay.verification_id
    assert integrated.entries[-1].parent_id == mapping.mapping_id
    assert len(integrated.entries) == len(final_gate_chain.entries) + 2
    assert integrated.chain_id


def test_chain_from_chain_accepts_ready_integration_mapping_with_explicit_gate_inputs() -> None:
    source_chain, gate, final_gate_replay, final_gate_chain, mapping, mapping_replay = (
        _mapping_inputs()
    )
    _ = source_chain
    with pytest.raises(
        TypeError,
        match="already integrated gate chain cannot receive gate/replay inputs",
    ):
        DashboardSessionFinalRecoveryGateAuditChain.from_chain(
            final_gate_chain,
            gate=gate,
            replay=final_gate_replay,
            integration_mapping=mapping,
            integration_mapping_replay=mapping_replay,
        )


def test_chain_from_chain_rejects_integration_mapping_without_replay() -> None:
    source_chain, _, final_gate_replay, final_gate_chain, mapping, _ = _mapping_inputs()
    _ = source_chain

    with pytest.raises(
        TypeError,
        match="integration_mapping_replay must be provided when integration_mapping is provided",
    ):
        DashboardSessionFinalRecoveryGateAuditChain.from_chain(
            final_gate_chain,
            integration_mapping=mapping,
            integration_mapping_replay=None,
        )


def test_chain_from_chain_rejects_mapping_with_gate_on_non_integrated_chain() -> None:
    source_chain, gate, final_gate_replay, _, mapping, mapping_replay = _mapping_inputs()

    non_integrated_mapping = type(mapping)(
        chain_id=source_chain.chain_id,
        chain_hash=source_chain.chain_hash,
        chain_entry_count=len(source_chain.entries),
        chain_replay_verification_id=(
            mapping.chain_replay_verification_id or mapping.chain_id
        ),
        full_audit_receipt_id=mapping.full_audit_receipt_id,
        full_audit_verification_id=mapping.full_audit_verification_id,
        binding_receipt_id=mapping.binding_receipt_id,
        integration_session_id=mapping.integration_session_id,
        previous_integration_session_id=mapping.previous_integration_session_id,
        decision="READY",
        reason_code="FORCED_READY_ON_SOURCE_CHAIN",
    )
    non_integrated_mapping_replay = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier().verify(
            non_integrated_mapping,
            non_integrated_mapping,
        )
    )

    with pytest.raises(
        ValueError,
        match="cannot bind mapping to a chain without integrated gate_replay",
    ):
        DashboardSessionFinalRecoveryGateAuditChain.from_chain(
            source_chain,
            gate=gate,
            replay=final_gate_replay,
            integration_mapping=non_integrated_mapping,
            integration_mapping_replay=non_integrated_mapping_replay,
        )


def test_chain_from_chain_rejects_mapping_without_gate_on_base_chain() -> None:
    source_chain, _, _, _, mapping, _ = _mapping_inputs()

    with pytest.raises(
        TypeError,
        match="gate must be a DashboardSessionFinalRecoveryChainReceipt",
    ):
        DashboardSessionFinalRecoveryGateAuditChain.from_chain(
            source_chain,
            integration_mapping=mapping,
            integration_mapping_replay=(
                DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier().verify(
                    mapping,
                    mapping,
                )
            ),
        )


def test_chain_from_chain_rejects_blocked_integration_mapping() -> None:
    source_chain, gate, final_gate_replay, final_gate_chain, mapping, mapping_replay = (
        _mapping_inputs()
    )
    _ = source_chain

    blocked = mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt(
        chain_id=mapping.chain_id,
        chain_hash=mapping.chain_hash,
        chain_entry_count=mapping.chain_entry_count,
        chain_replay_verification_id=mapping.chain_replay_verification_id,
        full_audit_receipt_id=mapping.full_audit_receipt_id,
        full_audit_verification_id=mapping.full_audit_verification_id,
        binding_receipt_id=mapping.binding_receipt_id,
        integration_session_id="integration-session",
        previous_integration_session_id=mapping.previous_integration_session_id,
        decision="BLOCKED",
        reason_code="FORCED",
    )
    blocked_replay = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier()
        .verify(blocked, blocked)
    )

    with pytest.raises(ValueError, match="cannot integrate a blocked mapping"):
        DashboardSessionFinalRecoveryGateAuditChain.from_chain(
            final_gate_chain,
            integration_mapping=blocked,
            integration_mapping_replay=blocked_replay,
        )


def test_chain_from_chain_accepts_persisted_integration_mapping(tmp_path) -> None:
    source_chain, gate, final_gate_replay, final_gate_chain, mapping, mapping_replay = (
        _mapping_inputs()
    )
    _ = source_chain
    _ = gate
    _ = final_gate_replay

    from smart_money.adapters.persistence import (
        dashboard_session_final_recovery_gate_audit_session_integration_mapping_store as store_model,
    )

    path = tmp_path / "integration-mappings.json"
    store = store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore(
        path
    )
    store.append(mapping)
    loaded = store.get(mapping.mapping_id)
    assert loaded == mapping

    loaded_replay = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier().verify(
            loaded,
            mapping,
        )
    )

    integrated = DashboardSessionFinalRecoveryGateAuditChain.from_chain(
        final_gate_chain,
        integration_mapping=loaded,
        integration_mapping_replay=loaded_replay,
    )

    assert integrated.entries[-2].entry_kind == "integration_mapping"
    assert integrated.entries[-1].entry_id == loaded_replay.verification_id
    assert integrated.chain_hash


def test_chain_from_chain_rejects_persisted_integration_mapping_with_mismatched_replay(
    tmp_path,
) -> None:
    source_chain, gate, final_gate_replay, final_gate_chain, mapping, mapping_replay = (
        _mapping_inputs()
    )
    _ = source_chain
    _ = gate
    _ = final_gate_replay

    from smart_money.adapters.persistence import (
        dashboard_session_final_recovery_gate_audit_session_integration_mapping_store as store_model,
    )

    path = tmp_path / "integration-mappings.json"
    store = store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore(
        path
    )
    store.append(mapping)
    loaded = store.get(mapping.mapping_id)
    assert loaded == mapping

    mismatched_replay = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier()
        .verify(mapping, mapping)
    )
    mismatched_replay = type(mismatched_replay)(
        expected_mapping_id=mismatched_replay.expected_mapping_id,
        actual_mapping_id="other-mapping-id",
        expected_full_audit_receipt_id=mismatched_replay.expected_full_audit_receipt_id,
        actual_full_audit_receipt_id=mismatched_replay.actual_full_audit_receipt_id,
        expected_full_audit_verification_id=mismatched_replay.expected_full_audit_verification_id,
        actual_full_audit_verification_id=mismatched_replay.actual_full_audit_verification_id,
        expected_binding_receipt_id=mismatched_replay.expected_binding_receipt_id,
        actual_binding_receipt_id=mismatched_replay.actual_binding_receipt_id,
        expected_chain_replay_verification_id=mismatched_replay.expected_chain_replay_verification_id,
        actual_chain_replay_verification_id=mismatched_replay.actual_chain_replay_verification_id,
        matches=False,
        mismatches=("actual_mapping_id",),
    )

    with pytest.raises(
        ValueError,
        match="integration mapping replay is not linked to mapping",
    ):
        DashboardSessionFinalRecoveryGateAuditChain.from_chain(
            final_gate_chain,
            integration_mapping=loaded,
            integration_mapping_replay=mismatched_replay,
        )


def test_chain_from_chain_rejects_integration_mapping_with_stale_chain_entry_count(
    tmp_path,
) -> None:
    source_chain, gate, final_gate_replay, final_gate_chain, mapping, mapping_replay = (
        _mapping_inputs()
    )
    _ = source_chain
    _ = gate
    _ = final_gate_replay

    stale_mapping = type(mapping)(
        chain_id=mapping.chain_id,
        chain_hash=mapping.chain_hash,
        chain_entry_count=mapping.chain_entry_count + 1,
        chain_replay_verification_id=mapping.chain_replay_verification_id,
        full_audit_receipt_id=mapping.full_audit_receipt_id,
        full_audit_verification_id=mapping.full_audit_verification_id,
        binding_receipt_id=mapping.binding_receipt_id,
        integration_session_id=mapping.integration_session_id,
        previous_integration_session_id=mapping.previous_integration_session_id,
        decision=mapping.decision,
        reason_code=mapping.reason_code,
    )

    stale_replay = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier()
        .verify(stale_mapping, stale_mapping)
    )

    with pytest.raises(
        ValueError,
        match="mapping is not linked to audit chain",
    ):
        DashboardSessionFinalRecoveryGateAuditChain.from_chain(
            final_gate_chain,
            integration_mapping=stale_mapping,
            integration_mapping_replay=stale_replay,
        )


def test_chain_from_chain_rejects_integration_mapping_with_stale_chain_hash(
    tmp_path,
) -> None:
    source_chain, gate, final_gate_replay, final_gate_chain, mapping, mapping_replay = (
        _mapping_inputs()
    )
    _ = source_chain
    _ = gate
    _ = final_gate_replay

    stale_mapping = type(mapping)(
        chain_id=mapping.chain_id,
        chain_hash="0" * 64,
        chain_entry_count=mapping.chain_entry_count,
        chain_replay_verification_id=mapping.chain_replay_verification_id,
        full_audit_receipt_id=mapping.full_audit_receipt_id,
        full_audit_verification_id=mapping.full_audit_verification_id,
        binding_receipt_id=mapping.binding_receipt_id,
        integration_session_id=mapping.integration_session_id,
        previous_integration_session_id=mapping.previous_integration_session_id,
        decision=mapping.decision,
        reason_code=mapping.reason_code,
    )

    stale_replay = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier()
        .verify(stale_mapping, stale_mapping)
    )

    with pytest.raises(
        ValueError,
        match="mapping is not linked to audit chain",
    ):
        DashboardSessionFinalRecoveryGateAuditChain.from_chain(
            final_gate_chain,
            integration_mapping=stale_mapping,
            integration_mapping_replay=stale_replay,
        )


def test_chain_from_chain_accepts_persisted_integration_mapping_replay(tmp_path) -> None:
    source_chain, gate, final_gate_replay, final_gate_chain, mapping, mapping_replay = (
        _mapping_inputs()
    )
    _ = source_chain
    _ = gate
    _ = final_gate_replay

    from smart_money.adapters.persistence import (
        dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_store as mapping_replay_store_model,
    )
    from smart_money.adapters.persistence import (
        dashboard_session_final_recovery_gate_audit_session_integration_mapping_store as mapping_store_model,
    )

    mapping_store_path = tmp_path / "integration-mapping-store.json"
    mapping_replay_store_path = tmp_path / "integration-mapping-replay-store.json"

    mapping_store = mapping_store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingStore(
        mapping_store_path
    )
    mapping_store.append(mapping)
    loaded_mapping = mapping_store.get(mapping.mapping_id)
    assert loaded_mapping == mapping

    mapping_replay_store = mapping_replay_store_model.JsonDashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayStore(
        mapping_replay_store_path
    )
    mapping_replay_store.append(mapping_replay)
    loaded_mapping_replay = mapping_replay_store.get(mapping_replay.verification_id)
    assert loaded_mapping_replay == mapping_replay

    replay_persistence = (
        mapping_replay_persistence_verifier.DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier(
            receipt_store=mapping_replay_store
        ).verify(mapping_replay)
    )
    assert replay_persistence.matches is True

    integrated = DashboardSessionFinalRecoveryGateAuditChain.from_chain(
        final_gate_chain,
        integration_mapping=loaded_mapping,
        integration_mapping_replay=loaded_mapping_replay,
    )

    assert integrated.entries[-2].entry_kind == "integration_mapping"
    assert integrated.entries[-1].entry_kind == "integration_mapping_replay"
    assert integrated.entries[-1].entry_id == loaded_mapping_replay.verification_id
    assert integrated.entries[-1].parent_id == loaded_mapping.mapping_id
