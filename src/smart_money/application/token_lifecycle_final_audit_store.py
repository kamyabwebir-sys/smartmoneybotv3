from __future__ import annotations
import json
from pathlib import Path
from smart_money.application.token_lifecycle_final_audit import TokenLifecycleFinalAuditReceipt

class TokenLifecycleFinalAuditStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, TokenLifecycleFinalAuditReceipt] = {}

    def save(self, receipt: TokenLifecycleFinalAuditReceipt) -> str:
        if not isinstance(receipt, TokenLifecycleFinalAuditReceipt):
            raise TypeError("receipt must be TokenLifecycleFinalAuditReceipt")
        self._items[receipt.audit_id] = receipt
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"schema_version":"token_lifecycle_final_audit_store.v1",
            "items":[r.canonical_dict() for r in self._items.values()]},
            sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return receipt.audit_id

    def get(self, audit_id: str) -> TokenLifecycleFinalAuditReceipt | None:
        return self._items.get(audit_id)

__all__ = ["TokenLifecycleFinalAuditStore"]
