from smart_money.adapters.persistence.durable_json_ledger import (
    DurableJsonEvidenceLedger,
)
from smart_money.adapters.solana_signature_ingestion import (
    bind_normalized_signature,
    bind_normalized_signature_batch,
)
from tests.adapters.test_solana_signature_normalizer import _buy_payload


def test_live_binding_is_durable_and_idempotent(tmp_path) -> None:
    path = tmp_path / "normalized-ledger.json"
    ledger = DurableJsonEvidenceLedger(path)
    first = bind_normalized_signature(ledger, _buy_payload())
    second = bind_normalized_signature(ledger, _buy_payload())

    assert first.evidence_id == second.evidence_id
    assert first.duplicate is False
    assert second.duplicate is True
    assert ledger.entry_count == 1
    assert DurableJsonEvidenceLedger(path).get(first.evidence_id) is not None


def test_historical_batch_binding_is_deterministic(tmp_path) -> None:
    ledger = DurableJsonEvidenceLedger(tmp_path / "batch.json")
    payload = _buy_payload()
    later = _buy_payload()
    later["slot"] = 43
    later["transaction"]["signatures"] = ["signature-2"]  # type: ignore[index]

    receipts = bind_normalized_signature_batch(ledger, (later, payload))

    assert tuple(item.signature for item in receipts) == (
        "signature-1",
        "signature-2",
    )
    assert ledger.entry_count == 2
