from __future__ import annotations

import hashlib
from dataclasses import dataclass

from smart_money.application import (
    dashboard_session_final_recovery_gate_audit_chain_replay_verifier as chain_replay_model,
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
from smart_money.application.dashboard_session_audit_chain import DashboardSessionAuditEntry
from smart_money.application.dashboard_session_final_recovery_gate_audit_chain import (
    DashboardSessionFinalRecoveryGateAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_gate_audit_full_audit_binding import (
    DashboardSessionFinalRecoveryGateAuditFullAuditBinder,
    DashboardSessionFinalRecoveryGateAuditFullAuditHeadAnchor,
)
from smart_money.core.serialization import canonical_json


@dataclass(frozen=True, slots=True)
class _ToyStore:
    mapping: dict[str, object]

    def get(self, verification_id: str) -> object | None:
        return self.mapping.get(verification_id)


def _chain_hash(entries: tuple[object, ...]) -> str:
    previous = "0" * 64
    for entry in entries:
        previous = hashlib.sha256(
            canonical_json(
                {"previous_hash": previous, "entry": entry.canonical_dict()}
            ).encode("utf-8")
        ).hexdigest()
    return previous


def _mutated_chain_with_extra_entry(
    base_chain: DashboardSessionFinalRecoveryGateAuditChain,
) -> DashboardSessionFinalRecoveryGateAuditChain:
    appended = base_chain.entries + (
        DashboardSessionAuditEntry(
            "binding-test",
            "test-extra-entry-id",
            None,
        ),
    )
    return DashboardSessionFinalRecoveryGateAuditChain(
        entries=appended,
        chain_hash=_chain_hash(appended),
    )


def _binding_inputs() -> tuple[
    DashboardSessionFinalRecoveryGateAuditChain,
    full_audit_model.DashboardSessionFinalRecoveryGateAuditRecoveryFullAuditReceipt,
]:
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
            chain,
            chain_replay,
            chain_replay,
        )
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
                {recovery_replay.verification_id: recovery_replay}
            ),
        ).verify(chain, chain_replay, recovery, recovery_replay)
    )

    return chain, full_audit


def test_binder_creates_head_anchor_for_full_audit() -> None:
    chain, full_audit = _binding_inputs()
    binder = DashboardSessionFinalRecoveryGateAuditFullAuditBinder()
    result = binder.bind(chain, full_audit)

    assert result.decision == "READY"
    assert result.reason_code == "FULL_AUDIT_CHAIN_BOUND"
    assert result.full_audit_id == full_audit.full_audit_id
    assert result.chain_id == chain.chain_id
    assert result.chain_hash == chain.chain_hash
    assert result.head_anchor_id != "missing-anchor"


def test_binder_rejects_chain_mismatch() -> None:
    chain, full_audit = _binding_inputs()
    bad_chain = _mutated_chain_with_extra_entry(chain)

    bad = DashboardSessionFinalRecoveryGateAuditFullAuditBinder().bind(
        bad_chain,
        full_audit,
    )

    assert bad.decision == "BLOCKED"
    assert bad.reason_code == "FULL_AUDIT_CHAIN_ID_MISMATCH"


def test_head_anchor_is_deterministic() -> None:
    chain, full_audit = _binding_inputs()
    binder = DashboardSessionFinalRecoveryGateAuditFullAuditBinder()
    first = binder.bind(chain, full_audit)
    second = binder.bind(chain, full_audit)

    assert first.head_anchor_id == second.head_anchor_id
    assert first.receipt_id == second.receipt_id


def test_binder_links_with_previous_anchor() -> None:
    chain, full_audit = _binding_inputs()
    binder = DashboardSessionFinalRecoveryGateAuditFullAuditBinder()
    first = binder.bind(chain, full_audit)
    previous_anchor = DashboardSessionFinalRecoveryGateAuditFullAuditHeadAnchor.from_chain(
        chain,
        full_audit,
        first.head_anchor_id,
    )
    expected_previous_anchor_id = previous_anchor.anchor_id
    second = binder.bind(
        chain,
        full_audit,
        previous_anchor=previous_anchor,
    )

    assert second.decision == "READY"
    assert second.previous_anchor_id == expected_previous_anchor_id
