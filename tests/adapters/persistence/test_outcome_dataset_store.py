from smart_money.adapters.persistence.outcome_dataset_store import OutcomeDatasetStore


def test_outcome_dataset_store_is_idempotent_and_recovers(tmp_path) -> None:
    store = OutcomeDatasetStore(tmp_path / "outcomes.json")
    document = {"schema_version": "mainnet_outcome_dataset.v1", "dataset_id": "d", "items": []}
    store.save(document)
    first = store.path.read_bytes()
    store.save(document)
    assert store.path.read_bytes() == first
    assert store.load() == document
