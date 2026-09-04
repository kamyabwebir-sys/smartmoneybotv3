from __future__ import annotations

import hashlib
from dataclasses import dataclass

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_verifier as chain_verifier_model,  # noqa: E501
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_persistence_verifier as replay_persistence_model,  # noqa: E501
)
from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditEntry,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapper import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_binding_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier,
)


@dataclass(frozen=True, slots=True)
class _ToyStore:
    values: dict[str, object]

    def get(self, key: str) -> object | None:
        return self.values.get(key)


@dataclass(frozen=True, slots=True)
class _ToyChain:
    entries: tuple[DashboardSessionAuditEntry, ...]
    chain_hash: str
    chain_id: str


_ChainPersistenceVerifier = (
    chain_verifier_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainPersistenceVerifier
)
_ReplayPersistenceVerifier = (
    replay_persistence_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayPersistenceVerifier
)


def _mapping(chain: _ToyChain) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt:
    return DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt(
        chain_id=chain.chain_id,
        chain_hash=chain.chain_hash,
        chain_entry_count=len(chain.entries),
        chain_replay_verification_id="chain-replay-id",
        full_audit_receipt_id="full-audit-id",
        full_audit_verification_id="full-audit-verification-id",
        binding_receipt_id="binding-id",
        integration_session_id="integration-session-id",
        previous_integration_session_id=None,
        decision="READY",
        reason_code="READY",
    )


def _mapping_replay(
    mapping: DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt:
    return DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayVerifier().verify(
        expected=mapping,
        actual=mapping,
    )


def _build_chain(
    include_replay: bool,
) -> tuple[
    _ToyChain,
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
    DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
]:
    chain_id = hashlib.sha256(b"mapping-chain-level-fixture").hexdigest()
    chain_hash = hashlib.sha256(b"mapping-chain-level-hash").hexdigest()
    chain = _ToyChain(entries=(), chain_hash=chain_hash, chain_id=chain_id)
    mapping = _mapping(chain)
    mapping = _replace_chain_count(mapping, 2 if include_replay else 1)
    mapping_replay = _mapping_replay(mapping)

    entries = (DashboardSessionAuditEntry("integration_mapping", mapping.mapping_id, None),)
    if include_replay:
        entries = entries + (
            DashboardSessionAuditEntry(
                "integration_mapping_replay",
                mapping_replay.verification_id,
                mapping.mapping_id,
            ),
        )
    return (
        _ToyChain(entries=entries, chain_hash=chain_hash, chain_id=chain_id),
        mapping,
        mapping_replay,
    )


def _verifier(
    chain: _ToyChain,
    mapping: DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
    mapping_replay: DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelVerifier:
    mapping_store = _ToyStore({mapping.mapping_id: mapping})
    replay_store = _ToyStore({mapping_replay.verification_id: mapping_replay})
    chain_persistence = _ChainPersistenceVerifier(
        mapping_store=mapping_store,
        replay_store=replay_store,
    )
    replay_persistence = _ReplayPersistenceVerifier(
        receipt_store=replay_store,
    )
    chain_binding = (
        DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainBindingVerifier(
            chain_persistence_verifier=chain_persistence,
            replay_persistence_verifier=replay_persistence,
        )
    )
    return DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingChainLevelVerifier(
        chain_binding_verifier=chain_binding,
        chain_persistence_verifier=chain_persistence,
        replay_persistence_verifier=replay_persistence,
    )


def _replace_chain_count(
    mapping: DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt,
    chain_entry_count: int,
) -> DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt:
    return DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt(
        chain_id=mapping.chain_id,
        chain_hash=mapping.chain_hash,
        chain_entry_count=chain_entry_count,
        chain_replay_verification_id=mapping.chain_replay_verification_id,
        full_audit_receipt_id=mapping.full_audit_receipt_id,
        full_audit_verification_id=mapping.full_audit_verification_id,
        binding_receipt_id=mapping.binding_receipt_id,
        integration_session_id=mapping.integration_session_id,
        previous_integration_session_id=mapping.previous_integration_session_id,
        decision=mapping.decision,
        reason_code=mapping.reason_code,
    )


def test_chain_level_verifier_ready() -> None:
    chain, mapping, mapping_replay = _build_chain(include_replay=True)
    receipt = _verifier(chain, mapping, mapping_replay).verify(
        chain=chain,
        mapping=mapping,
        mapping_replay=mapping_replay,
    )
    assert receipt.matches is True
    assert receipt.decision == "READY"
    assert receipt.chain_entry_mapping_presence is True
    assert receipt.chain_entry_mapping_replay_presence is True
    assert receipt.mismatches == ()


def test_chain_level_verifier_reports_chain_entry_count_mismatch() -> None:
    chain, mapping, mapping_replay = _build_chain(include_replay=True)
    stale_mapping = _replace_chain_count(mapping, len(chain.entries) + 1)
    stale_mapping_replay = _mapping_replay(stale_mapping)
    receipt = _verifier(chain, stale_mapping, stale_mapping_replay).verify(
        chain=chain,
        mapping=stale_mapping,
        mapping_replay=stale_mapping_replay,
    )
    assert receipt.matches is False
    assert "integration_mapping_chain_link_mismatch" in receipt.mismatches
    assert "chain_entry_count_mismatch" in receipt.mismatches


def test_chain_level_verifier_reports_missing_replay_entry() -> None:
    chain, mapping, mapping_replay = _build_chain(include_replay=False)
    receipt = _verifier(chain, mapping, mapping_replay).verify(
        chain=chain,
        mapping=mapping,
        mapping_replay=mapping_replay,
    )
    assert receipt.matches is False
    assert "mapping_replay_entry_missing_in_chain" in receipt.mismatches
    assert receipt.chain_entry_mapping_presence is True
    assert receipt.chain_entry_mapping_replay_presence is False
