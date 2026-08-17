from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from smart_money.adapters.persistence.historical_audit_manifest_store import (
    JsonHistoricalAuditManifestStore,
    JsonTrustedAuditHeadStore,
)
from smart_money.application.historical_receipt_audit import (
    HistoricalReceiptAuditManifest,
)
from smart_money.application.trusted_audit_head import (
    PrefixVerifiableHistoricalAuditStore,
    TrustedAuditHead,
    TrustedAuditHeadStatus,
    TrustedAuditHeadStore,
    TrustedAuditHeadVerificationError,
    advance_trusted_audit_head,
    make_trusted_audit_head,
    verify_trusted_audit_head,
    verify_trusted_audit_head_or_raise,
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


def _rejected_manifest(marker: str) -> HistoricalReceiptAuditManifest:
    payload: dict[str, object] = {
        "assessment_ids": (f"assessment-{marker}",),
        "conflict_count": 1,
        "corrupted_count": 0,
        "current_count": 0,
        "drifted_count": 0,
        "historically_valid_count": 0,
        "ledger_content_hash": marker * 64,
        "missing_count": 0,
        "receipt_count": 1,
        "receipt_store_hash": marker * 64,
        "rejected_receipt_ids": (f"receipt-{marker}",),
        "schema_version": "historical_receipt_audit.v1",
    }
    return HistoricalReceiptAuditManifest(
        audit_id=deterministic_id("historical_receipt_audit", payload),
        receipt_store_hash=marker * 64,
        ledger_content_hash=marker * 64,
        receipt_count=1,
        current_count=0,
        historically_valid_count=0,
        drifted_count=0,
        missing_count=0,
        corrupted_count=0,
        conflict_count=1,
        assessment_ids=(f"assessment-{marker}",),
        rejected_receipt_ids=(f"receipt-{marker}",),
    )


def _stores(tmp_path):
    manifests = JsonHistoricalAuditManifestStore(
        tmp_path / "historical-audits.json"
    )
    heads = JsonTrustedAuditHeadStore(tmp_path / "trusted-head.json")
    return manifests, heads


def test_initial_head_is_current_immutable_and_satisfies_ports(tmp_path) -> None:
    manifests, heads = _stores(tmp_path)
    manifests.append(_manifest("a"))

    head = advance_trusted_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )
    verification = verify_trusted_audit_head_or_raise(
        head=head,
        manifest_store=manifests,
    )

    assert isinstance(manifests, PrefixVerifiableHistoricalAuditStore)
    assert isinstance(heads, TrustedAuditHeadStore)
    assert verification.status is TrustedAuditHeadStatus.CURRENT
    assert head.manifest_count == 1
    assert head.latest_audit_id == _manifest("a").audit_id
    assert head.previous_anchor_id is None
    assert not hasattr(head, "__dict__")
    with pytest.raises(FrozenInstanceError):
        head.manifest_count = 0  # type: ignore[misc]


def test_valid_prefix_requires_advance_and_creates_monotonic_chain(
    tmp_path,
) -> None:
    manifests, heads = _stores(tmp_path)
    manifests.append(_manifest("a"))
    first = advance_trusted_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )
    manifests.append(_manifest("b"))

    stale = verify_trusted_audit_head(
        head=first,
        manifest_store=manifests,
    )
    second = advance_trusted_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )
    retained_bytes = heads.file_path.read_bytes()
    repeated = advance_trusted_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )

    assert stale.status is TrustedAuditHeadStatus.ADVANCE_REQUIRED
    assert second.previous_anchor_id == first.anchor_id
    assert second.manifest_count == 2
    assert repeated == second
    assert heads.file_path.read_bytes() == retained_bytes


def test_rollback_and_divergence_are_distinguished(tmp_path) -> None:
    source = JsonHistoricalAuditManifestStore(tmp_path / "source.json")
    source.append(_manifest("a"))
    source.append(_manifest("b"))
    head = make_trusted_audit_head(manifest_store=source)

    rolled_back = JsonHistoricalAuditManifestStore(tmp_path / "rollback.json")
    rolled_back.append(_manifest("a"))
    divergent = JsonHistoricalAuditManifestStore(tmp_path / "divergent.json")
    divergent.append(_manifest("a"))
    divergent.append(_manifest("c"))

    rollback = verify_trusted_audit_head(
        head=head,
        manifest_store=rolled_back,
    )
    divergence = verify_trusted_audit_head(
        head=head,
        manifest_store=divergent,
    )

    assert rollback.status is TrustedAuditHeadStatus.ROLLBACK
    assert divergence.status is TrustedAuditHeadStatus.DIVERGED
    with pytest.raises(TrustedAuditHeadVerificationError):
        verify_trusted_audit_head_or_raise(
            head=head,
            manifest_store=rolled_back,
        )


def test_head_store_rejects_branch_and_non_monotonic_replacement(
    tmp_path,
) -> None:
    manifests, heads = _stores(tmp_path)
    manifests.append(_manifest("a"))
    first = advance_trusted_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )
    manifests.append(_manifest("b"))
    second = advance_trusted_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )

    with pytest.raises(RuntimeError, match="chain mismatch"):
        heads.save(first)
    forged_payload = {
        **second.identity_payload(),
        "manifest_count": second.manifest_count,
        "previous_anchor_id": second.anchor_id,
    }
    non_advance = TrustedAuditHead(
        anchor_id=deterministic_id("trusted_audit_head", forged_payload),
        manifest_store_hash=second.manifest_store_hash,
        manifest_count=second.manifest_count,
        latest_audit_id=second.latest_audit_id,
        previous_anchor_id=second.anchor_id,
    )
    with pytest.raises(RuntimeError, match="advance monotonically"):
        heads.save(non_advance)


def test_trusted_head_tampering_is_detected(tmp_path) -> None:
    manifests, heads = _stores(tmp_path)
    manifests.append(_manifest("a"))
    advance_trusted_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )
    document = json.loads(heads.file_path.read_text(encoding="utf-8"))
    document["head"]["manifest_count"] = 0
    heads.file_path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        heads.load()


def test_orphaned_head_is_recovered_and_invalid_temp_is_retained(
    tmp_path,
) -> None:
    manifests, heads = _stores(tmp_path)
    manifests.append(_manifest("a"))
    head = advance_trusted_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )
    temporary_path = heads.file_path.with_name(
        f"{heads.file_path.name}.tmp"
    )
    heads.file_path.replace(temporary_path)

    assert heads.load() == head
    assert heads.file_path.is_file()
    assert not temporary_path.exists()

    invalid_path = tmp_path / "invalid-head.json"
    invalid_temp = tmp_path / "invalid-head.json.tmp"
    invalid_temp.write_text("{not-json", encoding="utf-8")
    invalid_store = JsonTrustedAuditHeadStore(invalid_path)
    with pytest.raises(ValueError, match="temporary trusted"):
        invalid_store.load()
    assert invalid_temp.is_file()


def test_forged_head_identity_is_rejected(tmp_path) -> None:
    manifests, _ = _stores(tmp_path)
    head = make_trusted_audit_head(manifest_store=manifests)

    with pytest.raises(ValueError, match="anchor_id"):
        TrustedAuditHead(
            **{
                **head.canonical_dict(),
                "anchor_id": "forged",
            }
        )


def test_rejected_manifest_cannot_be_anchored_or_advanced(tmp_path) -> None:
    manifests, heads = _stores(tmp_path)
    manifests.append(_rejected_manifest("a"))

    with pytest.raises(ValueError, match="rejected manifest"):
        make_trusted_audit_head(manifest_store=manifests)
    with pytest.raises(ValueError, match="rejected manifest"):
        advance_trusted_audit_head(
            manifest_store=manifests,
            head_store=heads,
        )

    accepted, accepted_heads = _stores(tmp_path / "accepted")
    accepted.append(_manifest("a"))
    head = advance_trusted_audit_head(
        manifest_store=accepted,
        head_store=accepted_heads,
    )
    accepted.append(_rejected_manifest("b"))

    with pytest.raises(ValueError, match="rejected manifest"):
        verify_trusted_audit_head(
            head=head,
            manifest_store=accepted,
        )
