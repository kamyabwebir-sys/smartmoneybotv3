from smart_money.application.backfill_ledger_binding import bind_backfill_batch
from smart_money.ingestion.ledger import EvidenceGroundingLedger


def test_backfill_binding_is_idempotent():
    ledger = EvidenceGroundingLedger()
    batch = ({"signature": "s1"},)
    first = bind_backfill_batch(ledger, batch, slot=10)
    second = bind_backfill_batch(ledger, batch, slot=10)
    assert first == second
    assert ledger.entry_count == 1
