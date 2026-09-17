from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from smart_money.application.production_shadow import BackfillCheckpoint, make_checkpoint, run_shadow_batch, verify_shadow_recovery


@dataclass(frozen=True, slots=True)
class ProductionEvaluation:
    processed: int
    failures: int
    ready: bool


def run_backfill_batch(fetcher: Callable[[int], Mapping[str, Any]], checkpoint: BackfillCheckpoint, *, batch_size: int = 10) -> tuple[tuple[Mapping[str, Any], ...], BackfillCheckpoint]:
    batch = run_shadow_batch(fetcher, checkpoint, batch_size=batch_size)
    return batch, make_checkpoint(checkpoint.next_slot + len(batch), checkpoint.processed + len(batch))


def run_shadow_session(fetcher: Callable[[int], Mapping[str, Any]], start_slot: int, *, batches: int = 1, batch_size: int = 10) -> tuple[Mapping[str, Any], ...]:
    checkpoint = make_checkpoint(start_slot, 0)
    outputs: list[Mapping[str, Any]] = []
    for _ in range(batches):
        batch, checkpoint = run_backfill_batch(fetcher, checkpoint, batch_size=batch_size)
        outputs.extend(batch)
    return tuple(outputs)


def evaluate_production(*, processed: int, failures: int, recovery_ok: bool) -> ProductionEvaluation:
    if processed < 0 or failures < 0:
        raise ValueError("evaluation counters must be non-negative")
    return ProductionEvaluation(processed, failures, processed > 0 and failures == 0 and recovery_ok)


__all__ = ["ProductionEvaluation", "run_backfill_batch", "run_shadow_session", "evaluate_production", "verify_shadow_recovery"]
