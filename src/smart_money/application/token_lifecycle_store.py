from __future__ import annotations

import json
from pathlib import Path

from smart_money.application.token_lifecycle import TokenLifecycle, TokenLifecycleState, build_token_lifecycle


class TokenLifecycleStore:
    """Small deterministic JSON store keyed by lifecycle_id."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, TokenLifecycle] = {}

    def save(self, lifecycle: TokenLifecycle) -> str:
        if not isinstance(lifecycle, TokenLifecycle):
            raise TypeError("lifecycle must be TokenLifecycle")
        self._items[lifecycle.lifecycle_id] = lifecycle
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._document(), sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return lifecycle.lifecycle_id

    def load(self) -> None:
        if not self.path.exists():
            return
        document = json.loads(self.path.read_text(encoding="utf-8"))
        if document.get("schema_version") != "token_lifecycle_store.v1" or not isinstance(document.get("items"), list):
            raise ValueError("invalid token lifecycle store")
        self._items = {}
        for item in document["items"]:
            lifecycle = build_token_lifecycle(
                item["token_id"], TokenLifecycleState(item["state"]),
                item["observed_slot"], tuple(item["evidence_ids"]),
            )
            if lifecycle.lifecycle_id != item.get("lifecycle_id"):
                raise ValueError("lifecycle identity mismatch")
            self._items[lifecycle.lifecycle_id] = lifecycle

    def get(self, lifecycle_id: str) -> TokenLifecycle | None:
        return self._items.get(lifecycle_id)

    def _document(self) -> dict[str, object]:
        return {"schema_version": "token_lifecycle_store.v1",
                "items": [self._items[key].canonical_dict() for key in sorted(self._items)]}


__all__ = ["TokenLifecycleStore"]
