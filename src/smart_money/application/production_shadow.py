from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


@dataclass(frozen=True, slots=True)
class SolanaRPCConfig:
    url: str
    network: str = "mainnet-beta"
    timeout_seconds: int = 10

    @classmethod
    def from_env(cls) -> "SolanaRPCConfig":
        url = os.getenv("SOLANA_RPC_URL", "").strip()
        if not url or not (url.startswith("https://") or url.startswith("http://")):
            raise ValueError("SOLANA_RPC_URL must be an HTTP(S) URL")
        return cls(url, os.getenv("SOLANA_NETWORK", "mainnet-beta").strip() or "mainnet-beta")


@dataclass(frozen=True, slots=True)
class BackfillCheckpoint:
    next_slot: int
    processed: int
    checkpoint_id: str


def make_checkpoint(next_slot: int, processed: int) -> BackfillCheckpoint:
    if next_slot < 0 or processed < 0:
        raise ValueError("checkpoint values must be non-negative")
    identity = f"{next_slot}:{processed}".encode()
    return BackfillCheckpoint(next_slot, processed, hashlib.sha256(identity).hexdigest())


class CheckpointedBackfill:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> BackfillCheckpoint:
        if not self.path.is_file():
            return make_checkpoint(0, 0)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return make_checkpoint(int(data["next_slot"]), int(data["processed"]))

    def save(self, checkpoint: BackfillCheckpoint) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps({"next_slot": checkpoint.next_slot, "processed": checkpoint.processed}, sort_keys=True), encoding="utf-8")
        temp.replace(self.path)


def run_shadow_batch(fetcher: Callable[[int], Mapping[str, Any]], checkpoint: BackfillCheckpoint, *, batch_size: int = 10) -> tuple[Mapping[str, Any], ...]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    results = tuple(fetcher(checkpoint.next_slot + index) for index in range(batch_size))
    if not all(isinstance(item, Mapping) for item in results):
        raise TypeError("shadow fetcher must return mappings")
    return results


def verify_shadow_recovery(before: BackfillCheckpoint, after: BackfillCheckpoint) -> bool:
    return after.next_slot >= before.next_slot and after.processed >= before.processed


__all__ = ["SolanaRPCConfig", "BackfillCheckpoint", "make_checkpoint", "CheckpointedBackfill", "run_shadow_batch", "verify_shadow_recovery"]
