from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from contracts import EvidencePayload
from ledger import EvidenceGroundingLedger


class ReplayEngine:
    """Replay validated persisted evidence in its recorded order."""

    def __init__(self, ledger_path: str | Path) -> None:
        self.ledger_path = Path(ledger_path)
        if not self.ledger_path.is_file():
            raise FileNotFoundError(f"persisted ledger not found: {self.ledger_path}")

        self._ledger = EvidenceGroundingLedger()
        self._ledger.load_from_disk(self.ledger_path)

    def stream_captured_evidence(self) -> Iterator[EvidencePayload]:
        for entry in self._ledger.get_all_entries():
            yield entry.payload

    @property
    def entry_count(self) -> int:
        return self._ledger.count
