from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from smart_money.application.early_entry_consistency import EarlyEntryConsistency
from smart_money.application.ports.evidence_ledger import EvidenceLedger


def load_early_entry_consistency_payload(
    payload_data: Mapping[str, Any],
) -> EarlyEntryConsistency:
    if not isinstance(payload_data, Mapping):
        raise TypeError("payload_data must be a mapping")
    required = {
        "wallet",
        "evaluated_buy_count",
        "early_entry_count",
        "consistency_bps",
        "token_ids",
        "activity_ids",
        "consistency_id",
        "schema_version",
    }
    if not required.issubset(payload_data):
        raise ValueError("early entry payload is missing required fields")
    optional = {
        key: payload_data[key]
        for key in ("observed_from_slot", "observed_to_slot")
        if key in payload_data
    }
    return EarlyEntryConsistency(
        wallet=payload_data["wallet"],
        evaluated_buy_count=payload_data["evaluated_buy_count"],
        early_entry_count=payload_data["early_entry_count"],
        consistency_bps=payload_data["consistency_bps"],
        token_ids=tuple(payload_data["token_ids"]),
        activity_ids=tuple(payload_data["activity_ids"]),
        consistency_id=payload_data["consistency_id"],
        schema_version=payload_data["schema_version"],
        **optional,
    )


def replay_early_entry_consistency_compatibility(
    ledger: EvidenceLedger,
) -> tuple[EarlyEntryConsistency, ...]:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    values: list[EarlyEntryConsistency] = []
    for payload in ledger.iter_payloads():
        if payload.evidence_type != "early_entry_consistency":
            continue
        data = payload.data.get("early_entry_consistency")
        values.append(load_early_entry_consistency_payload(data))
    return tuple(sorted(values, key=lambda item: item.consistency_id))


__all__ = [
    "load_early_entry_consistency_payload",
    "replay_early_entry_consistency_compatibility",
]
