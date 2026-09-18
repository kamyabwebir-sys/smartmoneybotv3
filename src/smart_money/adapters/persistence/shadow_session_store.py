from __future__ import annotations

import json
from pathlib import Path


class JsonShadowSessionStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, session_id: str, checkpoint_id: str, processed: int) -> str:
        if not session_id.strip() or not checkpoint_id.strip() or processed < 0:
            raise ValueError("invalid shadow session")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps({"schema_version": "shadow_session.v1", "session_id": session_id, "checkpoint_id": checkpoint_id, "processed": processed}, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)
        return session_id

    def load(self) -> dict[str, object]:
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != "shadow_session.v1":
            raise ValueError("unsupported shadow session schema")
        return data


__all__ = ["JsonShadowSessionStore"]
