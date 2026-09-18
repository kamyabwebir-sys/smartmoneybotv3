from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.historical_audit_manifest_store import (
    JsonHistoricalAuditManifestStore,
)
from smart_money.application.historical_receipt_audit import (
    HistoricalReceiptAuditManifest,
)
from smart_money.application.ports.historical_audit_manifest_store import (
    HistoricalAuditManifestStore,
)
from smart_money.core.ids import deterministic_id


def _manifest(marker: str) -> HistoricalReceiptAuditManifest:
    payload: dict[str, object] = {
        "assessment_ids": (f"assessment-{marker}",),
        "conflict_count": 0,
        "corrupted_count": 0,
        "current_count": 1,
        "drifted_count": 0,
        "historically_valid_count": 0,
        "ledger_content_hash": marker * 64,
        "missing_count": 0,
        "receipt_count": 1,
        "receipt_store_hash": marker * 64,
        "rejected_receipt_ids": (),
        "schema_version": "historical_receipt_audit.v1",
    }
    return HistoricalReceiptAuditManifest(
        audit_id=deterministic_id("historical_receipt_audit", payload),
        receipt_store_hash=marker * 64,
        ledger_content_hash=marker * 64,
        receipt_count=1,
        current_count=1,
        historically_valid_count=0,
        drifted_count=0,
        missing_count=0,
        corrupted_count=0,
        conflict_count=0,
        assessment_ids=(f"assessment-{marker}",),
        rejected_receipt_ids=(),
    )


def test_store_is_append_only_byte_stable_and_satisfies_port(tmp_path) -> None:
    path = tmp_path / "historical-audits.json"
    store = JsonHistoricalAuditManifestStore(path)
    first = _manifest("a")
    second = _manifest("b")

    first_id = store.append(first)
    first_bytes = path.read_bytes()
    duplicate_id = store.append(first)

    assert isinstance(store, HistoricalAuditManifestStore)
    assert first_id == duplicate_id == first.audit_id
    assert path.read_bytes() == first_bytes
    assert store.manifest_count == 1

    store.append(second)
    restored = JsonHistoricalAuditManifestStore(path)
    document = json.loads(path.read_text(encoding="utf-8"))

    assert tuple(restored.iter_manifests()) == (first, second)
    assert restored.get(first.audit_id) == first
    assert restored.get("missing") is None
    assert restored.manifest_count == 2
    assert restored.content_hash == document["content_hash"]
    assert (
        document["schema_version"]
        == "historical_audit_manifest_store.v1"
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda document: document.pop("content_hash"), "document keys"),
        (lambda document: document.update({"extra": True}), "document keys"),
        (
            lambda document: document.update({"schema_version": "store.v99"}),
            "unsupported",
        ),
        (
            lambda document: document.update({"content_hash": "NOT-A-HASH"}),
            "lowercase SHA-256",
        ),
        (
            lambda document: document.update({"manifests": {}}),
            "must be a list",
        ),
        (
            lambda document: document["manifests"][0].update({"extra": True}),
            "manifest keys",
        ),
        (
            lambda document: document["manifests"][0].update(
                {"assessment_ids": {}}
            ),
            "assessment_ids",
        ),
    ],
)
def test_store_schema_is_strict(tmp_path, mutation, message) -> None:
    path = tmp_path / "strict.json"
    JsonHistoricalAuditManifestStore(path).append(_manifest("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    mutation(document)
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        JsonHistoricalAuditManifestStore(path)


def test_manifest_tampering_is_detected_by_collection_hash(tmp_path) -> None:
    path = tmp_path / "tampered.json"
    JsonHistoricalAuditManifestStore(path).append(_manifest("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["manifests"][0]["current_count"] = 0
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        JsonHistoricalAuditManifestStore(path)


def test_forged_manifest_is_rejected_with_recomputed_hash(tmp_path) -> None:
    path = tmp_path / "forged.json"
    store = JsonHistoricalAuditManifestStore(path)
    store.append(_manifest("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["manifests"][0]["ledger_content_hash"] = "b" * 64
    document["content_hash"] = store._compute_content_hash(
        document["manifests"]
    )
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid historical"):
        JsonHistoricalAuditManifestStore(path)


def test_duplicate_identity_in_file_is_rejected(tmp_path) -> None:
    path = tmp_path / "duplicate.json"
    store = JsonHistoricalAuditManifestStore(path)
    store.append(_manifest("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["manifests"].append(document["manifests"][0])
    document["content_hash"] = store._compute_content_hash(
        document["manifests"]
    )
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate historical"):
        JsonHistoricalAuditManifestStore(path)


def test_valid_orphaned_temporary_store_is_recovered(tmp_path) -> None:
    path = tmp_path / "recoverable.json"
    temporary_path = tmp_path / "recoverable.json.tmp"
    manifest = _manifest("a")
    JsonHistoricalAuditManifestStore(path).append(manifest)
    path.replace(temporary_path)

    restored = JsonHistoricalAuditManifestStore(path)

    assert restored.get(manifest.audit_id) == manifest
    assert path.is_file()
    assert not temporary_path.exists()


def test_invalid_orphaned_temporary_store_is_retained(tmp_path) -> None:
    path = tmp_path / "invalid.json"
    temporary_path = tmp_path / "invalid.json.tmp"
    temporary_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="temporary historical audit"):
        JsonHistoricalAuditManifestStore(path)

    assert not path.exists()
    assert temporary_path.is_file()


def test_primary_store_remains_authoritative(tmp_path) -> None:
    path = tmp_path / "authoritative.json"
    temporary_path = tmp_path / "authoritative.json.tmp"
    primary = _manifest("a")
    JsonHistoricalAuditManifestStore(path).append(primary)
    primary_bytes = path.read_bytes()
    temporary_path.write_text("{not-json", encoding="utf-8")

    restored = JsonHistoricalAuditManifestStore(path)

    assert tuple(restored.iter_manifests()) == (primary,)
    assert path.read_bytes() == primary_bytes
    assert temporary_path.is_file()


def test_failed_append_does_not_mutate_in_memory_state(tmp_path) -> None:
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("blocked", encoding="utf-8")
    store = JsonHistoricalAuditManifestStore(
        blocked_parent / "audits.json"
    )

    with pytest.raises(OSError):
        store.append(_manifest("a"))

    assert store.manifest_count == 0


def test_append_rejects_non_manifest(tmp_path) -> None:
    store = JsonHistoricalAuditManifestStore(tmp_path / "audits.json")

    with pytest.raises(TypeError, match="HistoricalReceiptAuditManifest"):
        store.append(object())  # type: ignore[arg-type]
