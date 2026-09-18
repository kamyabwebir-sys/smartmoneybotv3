from pathlib import Path

import pytest

from smart_money.adapters.persistence.durable_run_receipt_audit_manifest_store import (
    JsonDurableRunReceiptAuditManifestStore,
)
from smart_money.application.durable_run_receipt_audit import (
    DurableRunReceiptAuditManifest,
)
from smart_money.core.ids import deterministic_id


def _manifest() -> DurableRunReceiptAuditManifest:
    zero = "0" * 64
    payload = {
        "assessments": (),
        "checkpoint_id": None,
        "commit_receipt_count": 0,
        "commit_receipt_store_hash": zero,
        "conflict_count": 0,
        "current_count": 0,
        "historically_valid_count": 0,
        "manifest_count": 0,
        "manifest_store_hash": zero,
        "ledger_content_hash": zero,
        "missing_prefix_count": 0,
        "rejected_run_ids": (),
        "run_count": 0,
        "run_store_hash": zero,
        "schema_version": "durable_run_receipt_audit.v1",
    }
    return DurableRunReceiptAuditManifest(
        audit_id=deterministic_id("durable_run_receipt_audit", payload),
        **payload,
    )


def test_store_round_trips_byte_stably_and_recovers_tmp(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.json"
    store = JsonDurableRunReceiptAuditManifestStore(path)
    manifest = _manifest()
    assert store.append(manifest) == manifest.audit_id
    first_bytes = path.read_bytes()
    assert store.append(manifest) == manifest.audit_id
    assert path.read_bytes() == first_bytes
    assert JsonDurableRunReceiptAuditManifestStore(path).get(
        manifest.audit_id
    ) == manifest
    assert store.contains_content_hash(store.content_hash, 1)
    path.replace(path.with_name("audit.json.tmp"))
    assert JsonDurableRunReceiptAuditManifestStore(path).get(
        manifest.audit_id
    ) == manifest


def test_store_rejects_corruption(tmp_path: Path) -> None:
    path = tmp_path / "audit.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="schema mismatch"):
        JsonDurableRunReceiptAuditManifestStore(path)
