from smart_money.application.wallet_intelligence_profile_store_audit import (
    build_wallet_intelligence_profile_store_audit,
)
from smart_money.application.wallet_intelligence_profile_store_replay import (
    WalletIntelligenceProfileStoreReplayReceipt,
)
from smart_money.core.ids import deterministic_id


def test_profile_store_audit_receipt_binds_save_load_and_replay() -> None:
    replay = WalletIntelligenceProfileStoreReplayReceipt(
        profile_id="profile-1",
        matches=True,
        replay_id=deterministic_id(
            "wallet_intelligence_profile_store_replay",
            {
                "matches": True,
                "profile_id": "profile-1",
                "schema_version": "wallet_intelligence_profile_store_replay.v1",
            },
        ),
    )
    receipt = build_wallet_intelligence_profile_store_audit(
        profile_id=" profile-1 ",
        save_id="save-1",
        load_id="load-1",
        replay_receipt=replay,
    )
    assert receipt.replay_matches is True
    assert receipt.profile_id == "profile-1"
    assert receipt.audit_id
