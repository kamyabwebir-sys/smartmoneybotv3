from pathlib import Path

import pytest

from smart_money.adapters.persistence.durable_run_receipt_audit_manifest_store import (
    JsonDurableRunReceiptAuditManifestStore,
    JsonTrustedDurableRunAuditHeadStore,
)
from smart_money.application.durable_run_audit_recovery_gate import (
    DurableRunAuditRecoveryGateStatus,
    FailClosedDurableRunAuditRecoveryGate,
)
from smart_money.application.trusted_durable_run_audit_head import (
    advance_trusted_durable_run_audit_head,
)
from tests.adapters.persistence.test_durable_run_receipt_audit_manifest_store import (
    _manifest,
)


@pytest.mark.parametrize("crash_target", ["manifest", "head"])
def test_restart_recovers_complete_temporary_documents(
    tmp_path: Path,
    crash_target: str,
) -> None:
    manifest_path = tmp_path / "audit.json"
    head_path = tmp_path / "head.json"
    manifests = JsonDurableRunReceiptAuditManifestStore(manifest_path)
    manifests.append(_manifest())
    heads = JsonTrustedDurableRunAuditHeadStore(head_path)
    advance_trusted_durable_run_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )
    target = manifest_path if crash_target == "manifest" else head_path
    target.replace(target.with_name(f"{target.name}.tmp"))

    recovered_manifests = JsonDurableRunReceiptAuditManifestStore(
        manifest_path
    )
    recovered_heads = JsonTrustedDurableRunAuditHeadStore(head_path)
    decision = FailClosedDurableRunAuditRecoveryGate(
        recovered_manifests,
        recovered_heads,
    ).open_or_raise()

    assert decision.status is DurableRunAuditRecoveryGateStatus.READY_CURRENT


def test_restart_fails_closed_on_corrupt_temporary_manifest(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.json"
    path.with_name("audit.json.tmp").write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="temporary"):
        JsonDurableRunReceiptAuditManifestStore(path)
