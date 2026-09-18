from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from smart_money.core.ids import deterministic_id


def execute_backfill_batch(
    fetcher: Callable[[int, int], tuple[Mapping[str, Any], ...]], batch: tuple[int, int]
) -> tuple[Mapping[str, Any], ...]:
    if not callable(fetcher) or len(batch) != 2 or batch[0] > batch[1]:
        raise ValueError("invalid batch")
    return fetcher(batch[0], batch[1])


def retry_transaction_batch(fetcher: Callable[[], Any], max_retries: int) -> Any:
    if not callable(fetcher) or max_retries < 0:
        raise ValueError("invalid retry policy")
    last: Exception | None = None
    for _ in range(max_retries + 1):
        try:
            return fetcher()
        except Exception as exc:
            last = exc
    raise RuntimeError("transaction batch failed") from last


class BackfillProgressStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, batch_index: int, completed: int) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"batch_index": batch_index, "completed": completed}, sort_keys=True
            ),
            encoding="utf-8",
        )

    def load(self) -> tuple[int, int]:
        if not self.path.exists():
            return (0, 0)
        value = json.loads(self.path.read_text(encoding="utf-8"))
        return int(value["batch_index"]), int(value["completed"])


def bind_historical_decoder(
    decoder: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    transaction: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not callable(decoder) or not isinstance(transaction, Mapping):
        raise TypeError("invalid decoder or transaction")
    result = decoder(transaction)
    if not isinstance(result, Mapping):
        raise TypeError("decoder result must be mapping")
    return result


def extract_historical_wallet_activity(
    decoded: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        {"wallet": item["wallet"], "token": item["token"], "slot": item.get("slot", 0)}
        for item in decoded.get("activities", ())
        if isinstance(item, Mapping) and item.get("wallet") and item.get("token")
    )


def extract_historical_token_activity(
    decoded: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        {"token": item["token"], "wallet": item["wallet"], "slot": item.get("slot", 0)}
        for item in decoded.get("activities", ())
        if isinstance(item, Mapping) and item.get("wallet") and item.get("token")
    )


def generate_historical_candidates(
    activities: tuple[Mapping[str, Any], ...],
) -> tuple[Mapping[str, Any], ...]:
    grouped: dict[tuple[str, str], int] = {}
    for item in activities:
        key = (str(item["wallet"]), str(item["token"]))
        grouped[key] = grouped.get(key, 0) + 1
    return tuple(
        {
            "wallet": w,
            "token": t,
            "activity_count": n,
            "candidate_id": deterministic_id(
                "historical_candidate",
                {
                    "activity_count": n,
                    "schema_version": "historical_candidate.v1",
                    "token": t,
                    "wallet": w,
                },
            ),
        }
        for (w, t), n in sorted(grouped.items())
    )


def join_candidate_outcomes(
    candidates: tuple[Mapping[str, Any], ...], outcomes: Mapping[str, Mapping[str, Any]]
) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        {**dict(item), "outcome": outcomes.get(item["candidate_id"])}
        for item in candidates
    )


@dataclass(frozen=True, slots=True)
class HistoricalDatasetAuditReport:
    record_count: int
    candidate_count: int
    report_id: str


def audit_historical_dataset(
    records: tuple[Mapping[str, Any], ...],
) -> HistoricalDatasetAuditReport:
    identity = {
        "candidate_count": sum("candidate_id" in x for x in records),
        "record_count": len(records),
        "schema_version": "historical_dataset_audit.v1",
    }
    return HistoricalDatasetAuditReport(
        identity["record_count"],
        identity["candidate_count"],
        deterministic_id("historical_dataset_audit", identity),
    )


def verify_historical_production_gate(
    checks: tuple[str, ...], passed: tuple[str, ...]
) -> bool:
    return bool(checks) and set(checks).issubset(passed)


__all__ = [
    "execute_backfill_batch",
    "retry_transaction_batch",
    "BackfillProgressStore",
    "bind_historical_decoder",
    "extract_historical_wallet_activity",
    "extract_historical_token_activity",
    "generate_historical_candidates",
    "join_candidate_outcomes",
    "HistoricalDatasetAuditReport",
    "audit_historical_dataset",
    "verify_historical_production_gate",
]
