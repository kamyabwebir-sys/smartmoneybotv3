from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.adapters.persistence.replay_integrity_store import (
    JsonReplayIntegrityStore,
)
from smart_money.analytics.scoring import MarketScorer
from smart_money.application.replay_integrity import (
    ReplayIntegrityManifest,
    create_replay_integrity_manifest,
)
from smart_money.core.replay import make_replay_manifest
from smart_money.ingestion.contracts import EvidencePayload


def _manifest(direction: str = "bullish") -> ReplayIntegrityManifest:
    ledger = EvidenceGroundingLedger()
    ledger.append(
        EvidencePayload(
            source_id="provider.sol",
            evidence_type="market_structure",
            timestamp=1_700_000_000,
            data={"direction": direction},
        )
    )
    report = MarketScorer().analyze(ledger.iter_payloads())
    replay_manifest = make_replay_manifest(
        pipeline_version="pipeline.v1",
        input_dataset_hash=ledger.content_hash,
        config_hash="config.v1",
    )
    return create_replay_integrity_manifest(
        replay_manifest=replay_manifest,
        ledger_content_hash=ledger.content_hash,
        report=report,
    )


def test_receipt_round_trip_is_byte_stable_and_content_addressed(tmp_path) -> None:
    store = JsonReplayIntegrityStore()
    manifest = _manifest()
    first_path = tmp_path / "first.receipt.json"
    second_path = tmp_path / "second.receipt.json"

    store.save(manifest, first_path)
    first_bytes = first_path.read_bytes()
    document = json.loads(first_bytes)
    restored = store.load(first_path)
    store.save(restored, second_path)

    assert restored == manifest
    assert second_path.read_bytes() == first_bytes
    assert document["schema_version"] == "replay_integrity_receipt.v1"
    assert len(document["content_hash"]) == 64
    assert document["manifest"] == manifest.canonical_dict()


def test_missing_receipt_fails_closed(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="receipt not found"):
        JsonReplayIntegrityStore().load(tmp_path / "missing.json")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda document: document.pop("content_hash"), "document keys"),
        (lambda document: document.update({"extra": True}), "document keys"),
        (
            lambda document: document.update({"schema_version": "receipt.v99"}),
            "unsupported",
        ),
        (
            lambda document: document.update({"content_hash": "NOT-A-HASH"}),
            "lowercase SHA-256",
        ),
        (
            lambda document: document["manifest"].update({"extra": True}),
            "manifest keys",
        ),
    ],
    ids=[
        "missing-content-hash",
        "extra-document-key",
        "unknown-schema",
        "malformed-content-hash",
        "extra-manifest-key",
    ],
)
def test_receipt_schema_is_strict(tmp_path, mutation, message) -> None:
    store = JsonReplayIntegrityStore()
    path = tmp_path / "strict.json"
    store.save(_manifest(), path)
    document = json.loads(path.read_text(encoding="utf-8"))
    mutation(document)
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        store.load(path)


def test_manifest_tampering_is_detected_by_receipt_hash(tmp_path) -> None:
    store = JsonReplayIntegrityStore()
    path = tmp_path / "tampered.json"
    store.save(_manifest(), path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["manifest"]["pipeline_version"] = "pipeline.v2"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        store.load(path)


def test_forged_manifest_is_rejected_even_with_recomputed_receipt_hash(
    tmp_path,
) -> None:
    store = JsonReplayIntegrityStore()
    path = tmp_path / "forged.json"
    store.save(_manifest(), path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["manifest"]["output_hash"] = "0" * 64
    document["content_hash"] = store._compute_content_hash(document["manifest"])
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid replay integrity manifest"):
        store.load(path)


def test_valid_orphaned_temporary_receipt_is_recovered(tmp_path) -> None:
    store = JsonReplayIntegrityStore()
    manifest = _manifest()
    path = tmp_path / "recoverable.json"
    temporary_path = tmp_path / "recoverable.json.tmp"
    store.save(manifest, path)
    path.replace(temporary_path)

    restored = store.load(path)

    assert restored == manifest
    assert path.is_file()
    assert not temporary_path.exists()


def test_invalid_orphaned_temporary_receipt_is_retained(tmp_path) -> None:
    path = tmp_path / "invalid-recovery.json"
    temporary_path = tmp_path / "invalid-recovery.json.tmp"
    temporary_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="temporary replay integrity recovery failed"):
        JsonReplayIntegrityStore().load(path)

    assert not path.exists()
    assert temporary_path.is_file()


def test_primary_receipt_remains_authoritative_when_temporary_exists(tmp_path) -> None:
    store = JsonReplayIntegrityStore()
    primary = _manifest("bullish")
    temporary = _manifest("bearish")
    path = tmp_path / "authoritative.json"
    temporary_source = tmp_path / "temporary-source.json"
    temporary_path = tmp_path / "authoritative.json.tmp"
    store.save(primary, path)
    store.save(temporary, temporary_source)
    temporary_path.write_bytes(temporary_source.read_bytes())

    restored = store.load(path)

    assert restored == primary
    assert temporary_path.is_file()
