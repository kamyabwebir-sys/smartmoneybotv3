from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from smart_money.application.dashboard_session_audit_chain import (
    DashboardSessionAuditEntry,
)
from smart_money.application.dashboard_session_final_recovery_audit_chain import (
    DashboardSessionFinalRecoveryAuditChain,
)
from smart_money.application.dashboard_session_final_recovery_chain_gate import (
    DashboardSessionFinalRecoveryChainReceipt,
)
from smart_money.application.dashboard_session_final_recovery_chain_replay_verifier import (
    DashboardSessionFinalRecoveryChainReplayReceipt,
)
from smart_money.core.serialization import canonical_json


@dataclass(frozen=True, slots=True)
class DashboardSessionFinalRecoveryGateAuditChain:
    entries: tuple[DashboardSessionAuditEntry, ...]
    chain_hash: str
    schema_version: str = "dashboard_session_final_recovery_gate_audit_chain.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple) or not all(
            isinstance(item, DashboardSessionAuditEntry) for item in self.entries
        ):
            raise TypeError("entries must be a tuple of audit entries")
        if self.chain_hash != _chain_hash(self.entries):
            raise ValueError("final recovery gate audit chain hash mismatch")
        if self.schema_version != "dashboard_session_final_recovery_gate_audit_chain.v1":
            raise ValueError("unsupported final recovery gate audit chain schema_version")

    @classmethod
    def from_chain(
        cls,
        chain: (
            DashboardSessionFinalRecoveryAuditChain | "DashboardSessionFinalRecoveryGateAuditChain"
        ),
        gate: DashboardSessionFinalRecoveryChainReceipt | None = None,
        replay: DashboardSessionFinalRecoveryChainReplayReceipt | None = None,
        integration_mapping: object | None = None,
        integration_mapping_replay: object | None = None,
    ) -> "DashboardSessionFinalRecoveryGateAuditChain":
        if not isinstance(
            chain,
            (
                DashboardSessionFinalRecoveryAuditChain,
                DashboardSessionFinalRecoveryGateAuditChain,
            ),
        ):
            raise TypeError(
                "chain must be a DashboardSessionFinalRecoveryAuditChain "
                "or DashboardSessionFinalRecoveryGateAuditChain"
            )
        is_gate_chain = isinstance(chain, DashboardSessionFinalRecoveryGateAuditChain)
        if is_gate_chain:
            if gate is not None or replay is not None:
                raise TypeError("already integrated gate chain cannot receive gate/replay inputs")
        else:
            if integration_mapping is not None and replay is not None and not isinstance(
                replay, DashboardSessionFinalRecoveryChainReplayReceipt
            ):
                raise ValueError(
                    "cannot bind mapping to a chain without integrated gate_replay"
                )
            if not isinstance(gate, DashboardSessionFinalRecoveryChainReceipt):
                raise TypeError("gate must be a DashboardSessionFinalRecoveryChainReceipt")
            if not isinstance(replay, DashboardSessionFinalRecoveryChainReplayReceipt):
                raise TypeError("replay must be a DashboardSessionFinalRecoveryChainReplayReceipt")
            if gate.decision != "READY":
                raise ValueError("cannot integrate a blocked gate receipt")
            if gate.chain_id != chain.chain_id:
                raise ValueError("gate receipt is not linked to recovery chain")
            if not replay.matches:
                raise ValueError("cannot integrate a non-matching gate replay")
            if replay.expected_receipt_id != gate.receipt_id:
                raise ValueError("gate replay is not linked to gate receipt")

        if integration_mapping is not None:
            from smart_money.application import (
                dashboard_session_final_recovery_gate_audit_session_integration_mapper as mapping_model,  # noqa: E501
            )
            from smart_money.application.dashboard_session_final_recovery_gate_audit_session_integration_mapping_replay_verifier import (  # noqa: E501
                DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt,
            )

            mapping_type = (
                mapping_model.DashboardSessionFinalRecoveryGateAuditSessionIntegrationReceipt
            )
            mapping_replay_type = (
                DashboardSessionFinalRecoveryGateAuditSessionIntegrationMappingReplayReceipt
            )
            if not isinstance(
                integration_mapping,
                mapping_type,
            ):
                raise TypeError("integration_mapping must be a valid integration mapping receipt")

            if not isinstance(
                integration_mapping_replay,
                mapping_replay_type,
            ):
                raise TypeError(
                    "integration_mapping_replay must be provided when "
                    "integration_mapping is provided"
                )

        entries = tuple(chain.entries)
        if isinstance(chain, DashboardSessionFinalRecoveryAuditChain):
            if gate.chain_id != chain.chain_id:
                raise ValueError("gate receipt is not linked to recovery chain")
            parent = chain.entries[-1].entry_id if chain.entries else None
            entries += (
                DashboardSessionAuditEntry("gate", gate.receipt_id, parent),
                DashboardSessionAuditEntry(
                    "gate_replay",
                    replay.verification_id,
                    gate.receipt_id,
                ),
            )
        else:
            if chain.entries[-1].entry_kind != "gate_replay":
                raise ValueError("cannot bind mapping to a chain without integrated gate_replay")

        if integration_mapping is not None:
            if (
                integration_mapping_replay.expected_mapping_id
                != integration_mapping.mapping_id
                or integration_mapping_replay.actual_mapping_id
                != integration_mapping.mapping_id
            ):
                raise ValueError("integration mapping replay is not linked to mapping")
            if not integration_mapping_replay.matches:
                raise ValueError("cannot integrate a non-matching mapping replay")
            if integration_mapping.decision != "READY":
                raise ValueError("cannot integrate a blocked mapping")
            if (
                integration_mapping.chain_id != chain.chain_id
                or integration_mapping.chain_hash != chain.chain_hash
                or integration_mapping.chain_entry_count != len(chain.entries)
            ):
                raise ValueError("mapping is not linked to audit chain")
            mapping_parent = entries[-1].entry_id
            entries = entries + (
                DashboardSessionAuditEntry(
                    "integration_mapping",
                    integration_mapping.mapping_id,
                    mapping_parent,
                ),
                DashboardSessionAuditEntry(
                    "integration_mapping_replay",
                    integration_mapping_replay.verification_id,
                    integration_mapping.mapping_id,
                ),
            )
        return cls(entries=entries, chain_hash=_chain_hash(entries))

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "chain_hash": self.chain_hash,
            "entries": [item.canonical_dict() for item in self.entries],
            "schema_version": self.schema_version,
        }

    @property
    def chain_id(self) -> str:
        return hashlib.sha256(canonical_json(self.canonical_dict()).encode("utf-8")).hexdigest()


def _chain_hash(entries: tuple[DashboardSessionAuditEntry, ...]) -> str:
    previous = "0" * 64
    for entry in entries:
        previous = hashlib.sha256(
            canonical_json({"previous_hash": previous, "entry": entry.canonical_dict()}).encode(
                "utf-8"
            )
        ).hexdigest()
    return previous


__all__ = ["DashboardSessionFinalRecoveryGateAuditChain"]
