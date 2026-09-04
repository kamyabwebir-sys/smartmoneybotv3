from __future__ import annotations

from dataclasses import dataclass

from smart_money.adapters.persistence import (
    dashboard_session_final_recovery_gate_audit_recovery_replay_store as replay_store,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_recovery_replay_verifier as replay_verifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain_replay_verifier import (
    DashboardSessionFinalRecoveryGateAuditChainReplayVerifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_gate import (
    DashboardSessionFinalRecoveryGateAuditRecoveryGate,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_replay_persistence_verifier import (
    DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceAuditReceipt,
    DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceVerifier,
)


def _recovery_replay() -> (
    replay_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt
):
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
    return replay_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier().verify(
        recovery, chain, chain_replay, chain_replay
    )


def test_persistence_verifier_confirms_round_tripped_replay(tmp_path) -> None:
    path = tmp_path / "replays.json"
    store = replay_store.JsonDashboardSessionFinalRecoveryGateAuditRecoveryReplayStore(path)
    expected = _recovery_replay()
    store.append(expected)

    result = DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceVerifier(
        receipt_store=store
    ).verify(expected)

    assert result.matches is True
    assert result.expected_verification_id == expected.verification_id
    assert result.persisted_verification_id == expected.verification_id
    assert result.mismatches == ()


@dataclass(frozen=True, slots=True)
class _ToyReceiptStore:
    mapping: dict[str, replay_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt]

    def get(self, verification_id: str):
        return self.mapping.get(verification_id)


@dataclass(frozen=True, slots=True)
class _SingleReceiptStore:
    receipt: replay_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt

    def get(self, verification_id: str):
        return self.receipt


def test_persistence_verifier_reports_mismatch_for_missing_receipt(tmp_path) -> None:
    expected = _recovery_replay()
    toy_store = _ToyReceiptStore(mapping={})
    result = DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceVerifier(
        receipt_store=toy_store
    ).verify(expected)

    assert result.matches is False
    assert result.persisted_verification_id is None
    assert result.mismatches == ("persisted_replay_receipt_missing",)


def test_persistence_verifier_reports_mismatch_for_payload_divergence() -> None:
    expected = _recovery_replay()
    altered = replay_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt(
        expected_receipt_id=expected.expected_receipt_id,
        actual_receipt_id=expected.actual_receipt_id,
        matches=False,
        mismatches=("reason_code",),
    )
    mismatching_store = _SingleReceiptStore(receipt=altered)

    result = DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceVerifier(
        receipt_store=mismatching_store
    ).verify(expected)

    assert result.matches is False
    assert result.persisted_verification_id == altered.verification_id
    assert result.mismatches == ("persisted_replay_receipt_mismatch",)


def test_persistence_audit_receipt_is_deterministic() -> None:
    expected = _recovery_replay()
    receipt_one = DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceAuditReceipt(
        expected_verification_id=expected.verification_id,
        persisted_verification_id=expected.verification_id,
        matches=True,
    )
    receipt_two = DashboardSessionFinalRecoveryGateAuditRecoveryReplayPersistenceAuditReceipt(
        expected_verification_id=expected.verification_id,
        persisted_verification_id=expected.verification_id,
        matches=True,
    )

    assert receipt_one == receipt_two
    assert receipt_one.audit_id == receipt_two.audit_id
