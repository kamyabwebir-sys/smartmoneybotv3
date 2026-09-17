from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from smart_money.application.backfill_decoder_binding import decode_and_bind_transaction
from smart_money.application.ports.evidence_ledger import EvidenceLedger


def replay_transaction_fixture(path: str | Path, ledger: EvidenceLedger) -> str:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("fixture root must be a mapping")
    return decode_and_bind_transaction(ledger, data)


def dashboard_shadow_read(ledger: EvidenceLedger) -> dict[str, Any]:
    payloads = tuple(ledger.iter_payloads())
    return {"schema_version": "shadow_dashboard_read.v1", "read_only": True, "evidence_count": len(payloads), "evidence_ids": tuple(item.get_canonical_id() for item in payloads)}


__all__ = ["replay_transaction_fixture", "dashboard_shadow_read"]
