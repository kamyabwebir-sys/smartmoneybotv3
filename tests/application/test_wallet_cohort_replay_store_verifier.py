from smart_money.adapters.persistence.wallet_cohort_replay_store import JsonWalletCohortReplayStore
from smart_money.application.wallet_cohort_replay import WalletCohortReplayReceipt
from smart_money.application.wallet_cohort_replay_store_verifier import verify_wallet_cohort_replay_store
from smart_money.core.ids import deterministic_id


def test_wallet_cohort_replay_store_verifier_matches_persisted_receipt(tmp_path) -> None:
    identity = {
        "cohort_id": "cohort-1",
        "matches": True,
        "schema_version": "wallet_cohort_replay.v1",
    }
    expected = WalletCohortReplayReceipt(
        **identity,
        replay_id=deterministic_id("wallet_cohort_replay", identity),
    )
    store = JsonWalletCohortReplayStore(tmp_path / "cohort-replay.json")
    store.append(expected)
    verification = verify_wallet_cohort_replay_store(store, expected)
    assert verification.matches is True
    assert verification.replay_id == expected.replay_id
    assert verification.verification_id
