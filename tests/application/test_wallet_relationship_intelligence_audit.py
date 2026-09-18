from smart_money.application.wallet_relationship_intelligence_audit import (
    build_wallet_relationship_intelligence_audit_receipt,
)
from smart_money.application.wallet_relationship_intelligence_replay import (
    WalletRelationshipIntelligenceReplayReceipt,
)
from smart_money.application.wallet_relationship_intelligence_store_verifier import (
    WalletRelationshipIntelligenceStoreVerificationReceipt,
)
from smart_money.core.ids import deterministic_id


def test_wallet_relationship_intelligence_audit_binds_replay_and_store() -> None:
    replay_identity = {
        "intelligence_id": "intelligence-1",
        "matches": True,
        "schema_version": "wallet_relationship_intelligence_replay.v1",
    }
    replay = WalletRelationshipIntelligenceReplayReceipt(
        **replay_identity,
        replay_id=deterministic_id(
            "wallet_relationship_intelligence_replay", replay_identity
        ),
    )
    verification_identity = {
        "intelligence_id": "intelligence-1",
        "matches": True,
        "schema_version": "wallet_relationship_intelligence_store_verifier.v1",
    }
    verification = WalletRelationshipIntelligenceStoreVerificationReceipt(
        **verification_identity,
        verification_id=deterministic_id(
            "wallet_relationship_intelligence_store_verification",
            verification_identity,
        ),
    )
    audit = build_wallet_relationship_intelligence_audit_receipt(
        intelligence_id="intelligence-1",
        replay_receipt=replay,
        store_verification=verification,
    )
    assert audit.replay_matches is True
    assert audit.audit_id
