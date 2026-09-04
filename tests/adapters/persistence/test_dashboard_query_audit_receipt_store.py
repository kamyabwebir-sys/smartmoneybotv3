from smart_money.adapters.persistence.dashboard_query_audit_receipt_store import (
    JsonDashboardQueryAuditReceiptStore,
)
from smart_money.application.dashboard_query_audit_receipt import (
    DashboardQueryAuditReceipt,
)


def _receipt() -> DashboardQueryAuditReceipt:
    return DashboardQueryAuditReceipt(
        query_id="query-1",
        status="SUCCESS",
        artifact_id="result-1",
        artifact_kind="result",
        output_hash="a" * 64,
        item_count=2,
        schema_versions=("query.v1", "result.v1"),
    )


def test_store_is_atomic_idempotent_and_recoverable(tmp_path) -> None:
    path = tmp_path / "dashboard-receipts.json"
    receipt = _receipt()
    store = JsonDashboardQueryAuditReceiptStore(path)

    assert store.append(receipt) == receipt.receipt_id
    assert store.append(receipt) == receipt.receipt_id
    assert store.receipt_count == 1

    reloaded = JsonDashboardQueryAuditReceiptStore(path)
    assert reloaded.get(receipt.receipt_id) == receipt
    assert reloaded.content_hash == store.content_hash
    assert ".tmp" not in path.read_text(encoding="utf-8")


def test_store_rejects_corruption(tmp_path) -> None:
    path = tmp_path / "dashboard-receipts.json"
    store = JsonDashboardQueryAuditReceiptStore(path)
    store.append(_receipt())
    path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")

    try:
        JsonDashboardQueryAuditReceiptStore(path)
    except ValueError as exc:
        assert "canonical" in str(exc) or "JSON" in str(exc)
    else:
        raise AssertionError("corrupted receipt store was accepted")
