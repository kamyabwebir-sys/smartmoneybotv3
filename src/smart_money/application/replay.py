from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.ingestion.contracts import EvidencePayload


class ReplayEngine:
    """Replay validated persisted evidence in deterministic recorded order."""

    def __init__(self, ledger_path: str | Path) -> None:
        self.ledger_path = Path(ledger_path)
        if not self.ledger_path.is_file():
            raise FileNotFoundError(f"persisted ledger not found: {self.ledger_path}")

        self._ledger = EvidenceGroundingLedger()
        self._ledger.load_from_disk(self.ledger_path)

    def stream_captured_evidence(self) -> Iterator[EvidencePayload]:
        yield from self._ledger.iter_payloads()

    @property
    def entry_count(self) -> int:
        return self._ledger.entry_count

    @property
    def content_hash(self) -> str:
        """Return the validated canonical hash of the loaded ledger."""
        return self._ledger.content_hash


__all__ = ["ReplayEngine"]
