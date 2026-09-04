from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.wallet_intelligence_profile import WalletIntelligenceProfile
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "wallet_intelligence_profile_store.v1"


class JsonWalletIntelligenceProfileStore:
    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._profile: WalletIntelligenceProfile | None = None
        self._load()

    def save(self, profile: WalletIntelligenceProfile) -> str:
        if not isinstance(profile, WalletIntelligenceProfile):
            raise TypeError("profile must be WalletIntelligenceProfile")
        if self._profile is not None and self._profile != profile:
            raise RuntimeError("wallet intelligence profile identity collision")
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {"profile": profile.canonical_dict(), "schema_version": _SCHEMA_VERSION}
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)
        self._profile = profile
        return profile.profile_id

    def load(self) -> WalletIntelligenceProfile | None:
        return self._profile

    def _load(self) -> None:
        if not self._file_path.is_file():
            return
        try:
            raw = self._file_path.read_text(encoding="utf-8")
            document: Any = json.loads(raw)
            if document["schema_version"] != _SCHEMA_VERSION:
                raise ValueError("unsupported wallet intelligence profile store schema_version")
            data = document["profile"]
            self._profile = WalletIntelligenceProfile(
                wallet=data["wallet"],
                observation_count=data["observation_count"],
                observed_from_slot=data["observed_from_slot"],
                observed_to_slot=data["observed_to_slot"],
                activity_count=data["activity_count"],
                buy_count=data["buy_count"],
                sell_count=data["sell_count"],
                unknown_count=data["unknown_count"],
                distinct_token_observation_total=data["distinct_token_observation_total"],
                token_delta_total=data["token_delta_total"],
                native_delta_total=data["native_delta_total"],
                data_completeness_bps=data["data_completeness_bps"],
                observation_ids=tuple(data["observation_ids"]),
                profile_id=data["profile_id"],
                schema_version=data["schema_version"],
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid wallet intelligence profile store") from exc
        if canonical_json(document) != raw:
            raise ValueError("wallet intelligence profile store is not canonical JSON")


__all__ = ["JsonWalletIntelligenceProfileStore"]
