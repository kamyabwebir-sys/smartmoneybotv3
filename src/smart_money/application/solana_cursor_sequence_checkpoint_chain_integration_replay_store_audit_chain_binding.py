from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store_verifier import (
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt:
    binding_id: str
    verification_id: str
    prior_audit_id: str
    matches: bool
    schema_version: str = (
        "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding.v1"
    )

    def __post_init__(self) -> None:
        for name in ("binding_id", "verification_id", "prior_audit_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.matches, bool):
            raise TypeError("matches must be boolean")
        if self.schema_version != (
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding.v1"
        ):
            raise ValueError("unsupported audit chain binding schema_version")
        expected = deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding",
            self.identity_payload(),
        )
        if self.binding_id != expected:
            raise ValueError("binding_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "matches": self.matches,
            "prior_audit_id": self.prior_audit_id,
            "schema_version": self.schema_version,
            "verification_id": self.verification_id,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"binding_id": self.binding_id, **self.identity_payload()}


def bind_solana_cursor_sequence_checkpoint_chain_integration_audit_chain(
    verification: SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStoreVerificationReceipt,
    prior_audit_id: str,
) -> SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt:
    if not isinstance(
        verification,
        SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStoreVerificationReceipt,
    ):
        raise TypeError("verification must be an audit replay store verification receipt")
    if not isinstance(prior_audit_id, str) or not prior_audit_id.strip():
        raise ValueError("prior_audit_id must be non-empty")
    identity = {
        "matches": verification.matches,
        "prior_audit_id": prior_audit_id.strip(),
        "schema_version": (
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding.v1"
        ),
        "verification_id": verification.verification_id,
    }
    return SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt(
        binding_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding",
            identity,
        ),
        verification_id=verification.verification_id,
        prior_audit_id=prior_audit_id.strip(),
        matches=verification.matches,
    )


__all__ = [
    "SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditChainBindingReceipt",
    "bind_solana_cursor_sequence_checkpoint_chain_integration_audit_chain",
]
