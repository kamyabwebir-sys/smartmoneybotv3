from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from smart_money.core.ids import deterministic_id
from smart_money.core.serialization import canonical_json


_NAMESPACE = "deterministic_config"
_VERSION_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_CONFIG_ID_PATTERN = re.compile(r"^deterministic_config_[0-9a-f]{32}$")


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be str")
    return value


def _require_non_empty_string(value: Any, field_name: str) -> str:
    text = _require_string(value, field_name)
    if text.strip() == "":
        raise ValueError(f"{field_name} must not be empty")
    return text


def _require_version(value: Any, field_name: str) -> str:
    version = _require_non_empty_string(value, field_name)
    if not _VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"{field_name} must match MAJOR.MINOR.PATCH")
    return version


def _require_sha256_hex(value: Any, field_name: str) -> str:
    digest = _require_non_empty_string(value, field_name)
    if not _SHA256_HEX_PATTERN.fullmatch(digest):
        raise ValueError(f"{field_name} must be 64 lowercase hex characters")
    return digest


def _require_config_id(value: Any, field_name: str) -> str:
    config_id = _require_non_empty_string(value, field_name)
    if not _CONFIG_ID_PATTERN.fullmatch(config_id):
        raise ValueError(f"{field_name} must match deterministic_config_<32 lowercase hex chars>")
    return config_id


def _validate_payload_json(payload_json: Any) -> tuple[str, dict[str, Any]]:
    payload_text = _require_non_empty_string(payload_json, "payload_json")

    try:
        parsed = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise ValueError("payload_json must be valid JSON") from exc

    if not isinstance(parsed, dict):
        raise ValueError("payload_json must decode to a JSON object")

    canonical_payload = canonical_json(parsed)
    if payload_text != canonical_payload:
        raise ValueError("payload_json must be canonical JSON")

    return payload_text, parsed


def _compute_payload_digest(payload_json: str) -> str:
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def _compute_config_id(
    *,
    config_kind: str,
    schema_version: str,
    config_version: str,
    payload_digest: str,
) -> str:
    return deterministic_id(
        _NAMESPACE,
        {
            "config_kind": config_kind,
            "schema_version": schema_version,
            "config_version": config_version,
            "payload_digest": payload_digest,
        },
    )


@dataclass(frozen=True)
class DeterministicConfig:
    config_kind: str
    schema_version: str
    config_version: str
    payload_json: str
    payload_digest: str
    config_id: str

    def __post_init__(self) -> None:
        config_kind = _require_non_empty_string(self.config_kind, "config_kind")
        schema_version = _require_version(self.schema_version, "schema_version")
        config_version = _require_version(self.config_version, "config_version")
        payload_json, _ = _validate_payload_json(self.payload_json)
        payload_digest = _require_sha256_hex(self.payload_digest, "payload_digest")
        config_id = _require_config_id(self.config_id, "config_id")

        expected_payload_digest = _compute_payload_digest(payload_json)
        if payload_digest != expected_payload_digest:
            raise ValueError("payload_digest does not match recomputed payload_digest")

        expected_config_id = _compute_config_id(
            config_kind=config_kind,
            schema_version=schema_version,
            config_version=config_version,
            payload_digest=payload_digest,
        )
        if config_id != expected_config_id:
            raise ValueError("config_id does not match recomputed config_id")

    def canonical_dict(self) -> dict[str, str]:
        return {
            "config_id": self.config_id,
            "config_kind": self.config_kind,
            "schema_version": self.schema_version,
            "config_version": self.config_version,
            "payload_json": self.payload_json,
            "payload_digest": self.payload_digest,
        }


@dataclass(frozen=True)
class ConfigVersionLock:
    config_kind: str
    schema_version: str
    config_version: str
    required_payload_digest: str | None = None
    required_config_id: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string(self.config_kind, "config_kind")
        _require_version(self.schema_version, "schema_version")
        _require_version(self.config_version, "config_version")

        if self.required_payload_digest is not None:
            _require_sha256_hex(self.required_payload_digest, "required_payload_digest")

        if self.required_config_id is not None:
            _require_config_id(self.required_config_id, "required_config_id")

    def is_satisfied_by(self, config: DeterministicConfig) -> bool:
        if not isinstance(config, DeterministicConfig):
            raise TypeError("config must be DeterministicConfig")

        if config.config_kind != self.config_kind:
            return False

        if config.schema_version != self.schema_version:
            return False

        if config.config_version != self.config_version:
            return False

        if self.required_payload_digest is not None:
            if config.payload_digest != self.required_payload_digest:
                return False

        if self.required_config_id is not None:
            if config.config_id != self.required_config_id:
                return False

        return True

    def canonical_dict(self) -> dict[str, str | None]:
        return {
            "config_kind": self.config_kind,
            "schema_version": self.schema_version,
            "config_version": self.config_version,
            "required_payload_digest": self.required_payload_digest,
            "required_config_id": self.required_config_id,
        }
