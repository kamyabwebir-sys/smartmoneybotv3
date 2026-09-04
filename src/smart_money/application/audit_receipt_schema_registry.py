from __future__ import annotations

# ruff: noqa: E501
from types import MappingProxyType
from typing import Mapping

_SCHEMA_VERSIONS = MappingProxyType(
    {
        "audit_recovery_gate": "audit_recovery_gate.v1",
        "commit_receipt_audit": "commit_receipt_audit.v1",
        "commit_receipt_verification": "commit_receipt_verification.v1",
        "durable_ingestion_commit": "durable_ingestion_commit.v1",
        "durable_recovery_gated_ingestion": "durable_recovery_gated_ingestion.v1",
        "chain_binding_persistence_replay": "dashboard_session_final_recovery_gate_audit_session_integration_mapping_chain_level_persistence_replay_store_chain_binding_persistence_replay.v1",
    }
)


def schema_version(receipt_kind: str) -> str:
    if not isinstance(receipt_kind, str) or not receipt_kind.strip():
        raise TypeError("receipt_kind must be a non-empty string")
    try:
        return _SCHEMA_VERSIONS[receipt_kind.strip()]
    except KeyError as exc:
        raise ValueError(f"unknown audit receipt schema: {receipt_kind}") from exc


def validate_schema_version(receipt_kind: str, value: object) -> str:
    expected = schema_version(receipt_kind)
    if value != expected:
        raise ValueError(
            f"unsupported {receipt_kind} schema_version: expected {expected}"
        )
    return expected


def registered_schema_versions() -> Mapping[str, str]:
    return _SCHEMA_VERSIONS


__all__ = [
    "registered_schema_versions",
    "schema_version",
    "validate_schema_version",
]
