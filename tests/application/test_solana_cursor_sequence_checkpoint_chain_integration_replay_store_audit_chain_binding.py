from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_chain_binding import (
    bind_solana_cursor_sequence_checkpoint_chain_integration_audit_chain,
)
from smart_money.application.solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store_verifier import (
    SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


def test_audit_chain_binding_is_deterministic():
    schema = "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store_verification.v1"
    verification = SolanaCursorSequenceCheckpointChainIntegrationReplayStoreAuditReplayStoreVerificationReceipt(
        verification_id=deterministic_id(
            "solana_cursor_sequence_checkpoint_chain_integration_replay_store_audit_replay_store_verification",
            {"matches": True, "replay_id": "replay", "schema_version": schema},
        ),
        replay_id="replay",
        matches=True,
    )
    binding = bind_solana_cursor_sequence_checkpoint_chain_integration_audit_chain(
        verification, "audit-1"
    )
    assert binding.matches is True
    assert binding.prior_audit_id == "audit-1"
