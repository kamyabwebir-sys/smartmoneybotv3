from smart_money.application.production_shadow import (
    CheckpointedBackfill,
    SolanaRPCConfig,
    make_checkpoint,
    run_shadow_batch,
    verify_shadow_recovery,
)


def test_secure_config_and_checkpoint_recovery(tmp_path, monkeypatch):
    monkeypatch.setenv("SOLANA_RPC_URL", "https://rpc.example")
    assert SolanaRPCConfig.from_env().network == "mainnet-beta"
    store = CheckpointedBackfill(tmp_path / "checkpoint.json")
    first = make_checkpoint(100, 10)
    store.save(first)
    assert store.load() == first
    second = make_checkpoint(110, 20)
    assert verify_shadow_recovery(first, second)


def test_shadow_batch_is_bounded():
    checkpoint = make_checkpoint(5, 0)
    result = run_shadow_batch(lambda slot: {"slot": slot}, checkpoint, batch_size=3)
    assert [item["slot"] for item in result] == [5, 6, 7]
