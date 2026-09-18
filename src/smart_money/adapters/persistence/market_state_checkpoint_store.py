from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.core.serialization import canonical_json
from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
)
from smart_money.domain.market_state import (
    MarketStateCheckpoint,
    MarketStateCursor,
)

_SCHEMA_VERSION = "market_state_checkpoint_store.v1"
_DOCUMENT_KEYS = frozenset({"schema_version", "content_hash", "checkpoint"})
_CHECKPOINT_KEYS = frozenset(
    {
        "checkpoint_id",
        "provider_id",
        "chain",
        "market",
        "cursor",
        "source_watermark",
        "reorder_window_blocks",
        "schema_version",
    }
)
_CHAIN_KEYS = frozenset({"namespace", "reference", "schema_version"})
_MARKET_KEYS = frozenset({"venue", "pair", "schema_version"})
_VENUE_KEYS = frozenset({"venue", "schema_version"})
_PAIR_KEYS = frozenset({"base", "quote", "schema_version"})
_ASSET_KEYS = frozenset(
    {"symbol", "chain", "contract_address", "schema_version"}
)
_CURSOR_KEYS = frozenset(
    {
        "provider_id",
        "chain",
        "chain_sequence",
        "event_index",
        "schema_version",
    }
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class JsonMarketStateCheckpointStore:
    """Persist one checkpoint as strict, byte-stable, recoverable JSON."""

    file_path: Path

    def __post_init__(self) -> None:
        if not isinstance(self.file_path, Path):
            object.__setattr__(self, "file_path", Path(self.file_path))

    def save(self, checkpoint: MarketStateCheckpoint) -> None:
        if not isinstance(checkpoint, MarketStateCheckpoint):
            raise TypeError("checkpoint must be a MarketStateCheckpoint")
        if self.file_path.parent != Path("."):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint_data = checkpoint.canonical_dict()
        document = {
            "schema_version": _SCHEMA_VERSION,
            "content_hash": self._compute_content_hash(checkpoint_data),
            "checkpoint": checkpoint_data,
        }
        temporary_path = self._temporary_path()
        with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary_path, self.file_path)

    def load(self) -> MarketStateCheckpoint:
        temporary_path = self._temporary_path()
        recovering_temporary_file = False
        if self.file_path.is_file():
            source_path = self.file_path
        elif temporary_path.is_file():
            source_path = temporary_path
            recovering_temporary_file = True
        else:
            raise FileNotFoundError(
                f"market-state checkpoint not found: {self.file_path}"
            )

        try:
            checkpoint = self._load_from_path(source_path)
        except ValueError as exc:
            if recovering_temporary_file:
                raise ValueError(
                    "temporary market-state checkpoint recovery failed: "
                    f"{temporary_path}"
                ) from exc
            raise
        if recovering_temporary_file:
            atomic_replace(temporary_path, self.file_path)
        return checkpoint

    def _load_from_path(self, path: Path) -> MarketStateCheckpoint:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"market-state checkpoint is not valid JSON: {path}"
            ) from exc
        if not isinstance(document, dict):
            raise ValueError("market-state checkpoint root must be an object")
        if set(document) != _DOCUMENT_KEYS:
            raise ValueError("checkpoint document keys do not match schema")
        if document["schema_version"] != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported checkpoint store schema_version: "
                f"{document['schema_version']}"
            )

        content_hash = document["content_hash"]
        if (
            not isinstance(content_hash, str)
            or _SHA256_PATTERN.fullmatch(content_hash) is None
        ):
            raise ValueError(
                "checkpoint content_hash must be a lowercase SHA-256 hex digest"
            )
        checkpoint_data = document["checkpoint"]
        self._validate_checkpoint_shape(checkpoint_data)
        expected_hash = self._compute_content_hash(checkpoint_data)
        if not hmac.compare_digest(content_hash, expected_hash):
            raise ValueError("market-state checkpoint content hash mismatch")
        try:
            return self._deserialize_checkpoint(checkpoint_data)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid market-state checkpoint payload") from exc

    @classmethod
    def _validate_checkpoint_shape(cls, checkpoint: Any) -> None:
        if not isinstance(checkpoint, dict):
            raise ValueError("checkpoint payload must be an object")
        if set(checkpoint) != _CHECKPOINT_KEYS:
            raise ValueError("checkpoint payload keys do not match schema")
        cls._require_keys(checkpoint["chain"], _CHAIN_KEYS, "chain")
        cls._require_keys(checkpoint["market"], _MARKET_KEYS, "market")
        cls._require_keys(checkpoint["market"]["venue"], _VENUE_KEYS, "venue")
        cls._require_keys(checkpoint["market"]["pair"], _PAIR_KEYS, "pair")
        cls._require_asset(checkpoint["market"]["pair"]["base"], "base")
        cls._require_asset(checkpoint["market"]["pair"]["quote"], "quote")
        cls._require_keys(checkpoint["cursor"], _CURSOR_KEYS, "cursor")
        cls._require_keys(checkpoint["cursor"]["chain"], _CHAIN_KEYS, "cursor chain")

    @classmethod
    def _require_asset(cls, value: Any, field_name: str) -> None:
        cls._require_keys(value, _ASSET_KEYS, field_name)
        if value["chain"] is not None:
            cls._require_keys(value["chain"], _CHAIN_KEYS, f"{field_name} chain")

    @staticmethod
    def _require_keys(
        value: Any,
        expected_keys: frozenset[str],
        field_name: str,
    ) -> None:
        if not isinstance(value, dict):
            raise ValueError(f"checkpoint {field_name} must be an object")
        if set(value) != expected_keys:
            raise ValueError(
                f"checkpoint {field_name} keys do not match schema"
            )

    @classmethod
    def _deserialize_checkpoint(
        cls,
        data: dict[str, Any],
    ) -> MarketStateCheckpoint:
        chain = cls._chain(data["chain"])
        market_data = data["market"]
        pair_data = market_data["pair"]
        market = MarketId(
            venue=VenueId(**market_data["venue"]),
            pair=PairId(
                base=cls._asset(pair_data["base"]),
                quote=cls._asset(pair_data["quote"]),
                schema_version=pair_data["schema_version"],
            ),
            schema_version=market_data["schema_version"],
        )
        cursor_data = data["cursor"]
        cursor = MarketStateCursor(
            provider_id=cursor_data["provider_id"],
            chain=cls._chain(cursor_data["chain"]),
            chain_sequence=cursor_data["chain_sequence"],
            event_index=cursor_data["event_index"],
            schema_version=cursor_data["schema_version"],
        )
        return MarketStateCheckpoint(
            checkpoint_id=data["checkpoint_id"],
            provider_id=data["provider_id"],
            chain=chain,
            market=market,
            cursor=cursor,
            source_watermark=data["source_watermark"],
            reorder_window_blocks=data["reorder_window_blocks"],
            schema_version=data["schema_version"],
        )

    @classmethod
    def _asset(cls, data: dict[str, Any]) -> AssetId:
        chain_data = data["chain"]
        return AssetId(
            symbol=data["symbol"],
            chain=None if chain_data is None else cls._chain(chain_data),
            contract_address=data["contract_address"],
            schema_version=data["schema_version"],
        )

    @staticmethod
    def _chain(data: dict[str, Any]) -> ChainId:
        return ChainId(**data)

    @staticmethod
    def _compute_content_hash(checkpoint_data: dict[str, Any]) -> str:
        material = {
            "schema_version": _SCHEMA_VERSION,
            "checkpoint": checkpoint_data,
        }
        return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()

    def _temporary_path(self) -> Path:
        return self.file_path.with_name(f"{self.file_path.name}.tmp")


__all__ = ["JsonMarketStateCheckpointStore"]
