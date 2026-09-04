from __future__ import annotations
import json
from pathlib import Path
from smart_money.application.cross_intelligence import WalletTokenCrossSubjectContract

class CrossIntelligenceStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, WalletTokenCrossSubjectContract] = {}
    def save(self, contract: WalletTokenCrossSubjectContract) -> str:
        if not isinstance(contract, WalletTokenCrossSubjectContract):
            raise TypeError("contract must be WalletTokenCrossSubjectContract")
        self._items[contract.cross_id] = contract
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"schema_version":"cross_intelligence_store.v1","items":[x.canonical_dict() for x in self._items.values()]}, sort_keys=True, separators=(",",":")), encoding="utf-8")
        return contract.cross_id
    def get(self, cross_id: str) -> WalletTokenCrossSubjectContract | None:
        return self._items.get(cross_id)

__all__ = ["CrossIntelligenceStore"]
