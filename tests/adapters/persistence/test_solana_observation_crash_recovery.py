from __future__ import annotations

from smart_money.adapters.persistence.solana_observation_store import (
    JsonSolanaObservationStore,
)
from smart_money.adapters.solana_signature_normalizer import (
    SolanaSignatureNormalizer,
)
from smart_money.application.solana_observation_parser import (
    SolanaObservationParser,
)
from tests.adapters.test_solana_signature_normalizer import _buy_payload


def test_normalized_observation_is_idempotent_and_recovers_from_tmp(tmp_path) -> None:
    observation = SolanaSignatureNormalizer.normalize(_buy_payload()).observation
    payload = SolanaObservationParser.from_observation(observation).payload
    path = tmp_path / "solana-observations.json"
    store = JsonSolanaObservationStore(path)

    evidence_id = store.append(payload)
    assert store.append(payload) == evidence_id
    baseline_hash = store.content_hash
    assert store.entry_count == 1

    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_bytes(path.read_bytes())
    path.unlink()

    recovered = JsonSolanaObservationStore(path)
    receipt = recovered.replay(observation)

    assert recovered.entry_count == 1
    assert recovered.content_hash == baseline_hash
    assert recovered.get(evidence_id) == payload
    assert receipt.matches is True
    assert receipt.observation_id == observation.observation_id
    assert not temporary.exists()
