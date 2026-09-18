from __future__ import annotations

from dataclasses import dataclass

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_chain_replay_verifier as chain_replay_verifier,
)
from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_recovery_full_audit_verifier as full_audit_verifier,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_gate import (
    DashboardSessionFinalRecoveryGateAuditRecoveryGate,
    DashboardSessionFinalRecoveryGateAuditRecoveryReceipt,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_recovery_replay_verifier import (  # noqa: E501
    DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt,
    DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier,
)


def _receipt_pair() -> tuple[
    DashboardSessionFinalRecoveryGateAuditChain,
    chain_replay_verifier.DashboardSessionFinalRecoveryGateAuditChainReplayReceipt,
    DashboardSessionFinalRecoveryGateAuditRecoveryReceipt,
    DashboardSessionFinalRecoveryGateAuditRecoveryReplayReceipt,
]:
    chain = DashboardSessionFinalRecoveryGateAuditChain(
        entries=(),
        chain_hash="0" * 64,
    )
    chain_replay = (
        chain_replay_verifier.DashboardSessionFinalRecoveryGateAuditChainReplayVerifier()
        .verify(chain, chain)
    )
    expected = DashboardSessionFinalRecoveryGateAuditRecoveryGate().evaluate(
        chain, chain_replay, chain_replay
    )
    recovery_replay = (
        DashboardSessionFinalRecoveryGateAuditRecoveryReplayVerifier().verify(
            expected, chain, chain_replay, chain_replay
        )
    )
    return chain, chain_replay, expected, recovery_replay


@dataclass(frozen=True, slots=True)
class _ToyStore:
    mapping: dict[str, object]

    def get(self, verification_id: str):
        return self.mapping.get(verification_id)


def test_full_audit_verifier_passes_with_persisted_round_trips() -> None:
    chain, chain_replay, expected, recovery_replay = _receipt_pair()
    result = (
        full_audit_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier(
            chain_replay_store=_ToyStore({chain_replay.verification_id: chain_replay}),
            recovery_replay_store=_ToyStore(
                {recovery_replay.verification_id: recovery_replay}
            ),
        ).verify(chain, chain_replay, expected, recovery_replay)
    )

    assert result.matches is True
    assert result.expected_chain_id == chain.chain_id
    assert result.chain_replay_verification_id == chain_replay.verification_id
    assert result.recovery_replay_verification_id == recovery_replay.verification_id
    assert result.full_audit_id


def test_full_audit_verifier_detects_missing_recoveries() -> None:
    chain, chain_replay, expected, recovery_replay = _receipt_pair()
    result = (
        full_audit_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier().verify(
            chain, chain_replay, expected, recovery_replay
        )
    )

    assert result.matches is False
    assert result.persisted_chain_replay_verification_id is None
    assert result.persisted_recovery_replay_verification_id is None
    assert (
        "persisted_gate_audit_chain_replay_store_missing"
        in result.mismatches
        and "persisted_gate_audit_recovery_replay_store_missing"
        in result.mismatches
    )


def test_full_audit_verifier_detects_linkage_drift() -> None:
    chain, chain_replay, expected, recovery_replay = _receipt_pair()
    altered_expected = DashboardSessionFinalRecoveryGateAuditRecoveryReceipt(
        decision="READY",
        reason_code=expected.reason_code,
        chain_id="different",
        replay_verification_id=expected.replay_verification_id,
        schema_version=expected.schema_version,
    )
    result = (
        full_audit_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier().verify(
            chain, chain_replay, altered_expected, recovery_replay
        )
    )

    assert result.matches is False
    assert "recovery_gate_chain_id" in result.mismatches


def test_full_audit_receipt_is_deterministic() -> None:
    chain, chain_replay, expected, recovery_replay = _receipt_pair()
    result_one = (
        full_audit_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier(
            chain_replay_store=_ToyStore({chain_replay.verification_id: chain_replay}),
            recovery_replay_store=_ToyStore(
                {recovery_replay.verification_id: recovery_replay}
            ),
        ).verify(chain, chain_replay, expected, recovery_replay)
    )
    result_two = (
        full_audit_verifier.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditVerifier(
            chain_replay_store=_ToyStore({chain_replay.verification_id: chain_replay}),
            recovery_replay_store=_ToyStore(
                {recovery_replay.verification_id: recovery_replay}
            ),
        ).verify(chain, chain_replay, expected, recovery_replay)
    )

    assert result_one == result_two
    assert result_one.full_audit_id == result_two.full_audit_id
