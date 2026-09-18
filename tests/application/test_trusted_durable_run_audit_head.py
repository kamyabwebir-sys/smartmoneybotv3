from pathlib import Path

import pytest

from smart_money.adapters.persistence.durable_run_receipt_audit_manifest_store import (
    JsonDurableRunReceiptAuditManifestStore,
    JsonTrustedDurableRunAuditHeadStore,
)
from smart_money.application.trusted_durable_run_audit_head import (
    TrustedDurableRunAuditHeadStatus,
    advance_trusted_durable_run_audit_head,
    verify_trusted_durable_run_audit_head,
)
from tests.adapters.persistence.test_durable_run_receipt_audit_manifest_store import (
    _manifest,
)


def test_head_is_current_and_persists_atomically(tmp_path: Path) -> None:
    manifests = JsonDurableRunReceiptAuditManifestStore(tmp_path / "audit.json")
    manifests.append(_manifest())
    heads = JsonTrustedDurableRunAuditHeadStore(tmp_path / "head.json")
    head = advance_trusted_durable_run_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )
    assert heads.load() == head
    assert (
        verify_trusted_durable_run_audit_head(
            head=head,
            manifest_store=manifests,
        ).status
        is TrustedDurableRunAuditHeadStatus.CURRENT
    )


def test_head_rejects_manifest_with_rejected_runs(tmp_path: Path) -> None:
    manifests = JsonDurableRunReceiptAuditManifestStore(tmp_path / "audit.json")
    bad = _manifest()
    manifests.append(bad)
    object.__setattr__(bad, "conflict_count", 1)
    object.__setattr__(bad, "run_count", 1)
    with pytest.raises(ValueError):
        advance_trusted_durable_run_audit_head(
            manifest_store=manifests,
            head_store=JsonTrustedDurableRunAuditHeadStore(
                tmp_path / "head.json"
            ),
        )
