from __future__ import annotations

from typing import Any, Mapping

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.ingestion.contracts import EvidencePayload


def bind_backfill_batch(ledger: EvidenceLedger, batch: tuple[Mapping[str, Any], ...], *, slot: int) -> tuple[str, ...]:
    if not isinstance(slot, int) or slot < 0 or not batch:
        raise ValueError("invalid backfill batch")
    ids = []
    for item in batch:
        payload = EvidencePayload("solana-backfill", "solana_rpc_transaction", slot, {"response": dict(item)}, {"classification": "EVIDENCE", "verification_status": "UNKNOWN"})
        ids.append(ledger.append(payload))
    return tuple(ids)


__all__ = ["bind_backfill_batch"]
