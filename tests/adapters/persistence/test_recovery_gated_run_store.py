from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence.recovery_gated_run_store import (
    JsonRecoveryGatedRunStore,
)
from smart_money.application.audit_recovery_gate import (
    AuditRecoveryGateDecision,
    AuditRecoveryGateStatus,
)
from smart_money.application.checkpointed_ingestion import (
    CheckpointedIngestionResult,
)
from smart_money.application.ports.recovery_gated_run_store import (
    RecoveryGatedRunStore,
)
from smart_money.application.recovery_gated_ingestion import (
    RecoveryGatedIngestionResult,
)
from smart_money.core.ids import deterministic_id


def _result(marker: str) -> RecoveryGatedIngestionResult:
    gate_payload: dict[str, object] = {
        "advance_requested": False,
        "allowed": True,
        "latest_audit_id": f"audit-{marker}",
        "manifest_count": 1,
        "manifest_store_hash": marker * 64,
        "schema_version": "audit_recovery_gate.v1",
        "status": AuditRecoveryGateStatus.READY_CURRENT.value,
        "trusted_anchor_id": f"anchor-{marker}",
        "verification_id": f"verification-{marker}",
    }
    gate = AuditRecoveryGateDecision(
        decision_id=deterministic_id("audit_recovery_gate", gate_payload),
        status=AuditRecoveryGateStatus.READY_CURRENT,
        allowed=True,
        advance_requested=False,
        trusted_anchor_id=f"anchor-{marker}",
        verification_id=f"verification-{marker}",
        manifest_store_hash=marker * 64,
        manifest_count=1,
        latest_audit_id=f"audit-{marker}",
    )
    ingestion_payload: dict[str, object] = {
        "accepted_count": 0,
        "final_checkpoint_id": None,
        "first_accepted_event_id": None,
        "last_accepted_event_id": None,
        "market_id": f"market-{marker}",
        "provider_id": f"provider-{marker}",
        "resumed_from_checkpoint_id": None,
        "schema_version": "checkpointed_ingestion_result.v1",
    }
    ingestion = CheckpointedIngestionResult(
        session_id=deterministic_id(
            "checkpointed_ingestion_result",
            ingestion_payload,
        ),
        provider_id=f"provider-{marker}",
        market_id=f"market-{marker}",
        resumed_from_checkpoint_id=None,
        first_accepted_event_id=None,
        last_accepted_event_id=None,
        accepted_count=0,
        final_checkpoint_id=None,
    )
    payload: dict[str, object] = {
        "gate_decision": gate.canonical_dict(),
        "ingestion_result": ingestion.canonical_dict(),
        "requested_max_events": 1,
        "schema_version": "recovery_gated_ingestion.v1",
    }
    return RecoveryGatedIngestionResult(
        run_id=deterministic_id("recovery_gated_ingestion", payload),
        gate_decision=gate,
        ingestion_result=ingestion,
        requested_max_events=1,
    )


def test_store_is_append_only_byte_stable_and_satisfies_port(tmp_path) -> None:
    path = tmp_path / "recovery-runs.json"
    store = JsonRecoveryGatedRunStore(path)
    first = _result("a")
    second = _result("b")

    first_id = store.append(first)
    first_bytes = path.read_bytes()
    duplicate_id = store.append(first)

    assert isinstance(store, RecoveryGatedRunStore)
    assert first_id == duplicate_id == first.run_id
    assert path.read_bytes() == first_bytes
    assert store.result_count == 1

    store.append(second)
    restored = JsonRecoveryGatedRunStore(path)
    document = json.loads(path.read_text(encoding="utf-8"))

    assert tuple(restored.iter_results()) == (first, second)
    assert restored.get(first.run_id) == first
    assert restored.get("missing") is None
    assert restored.result_count == 2
    assert restored.content_hash == document["content_hash"]
    assert document["schema_version"] == "recovery_gated_run_store.v1"


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
            lambda document: document.update({"results": {}}),
            "must be a list",
        ),
        (
            lambda document: document["results"][0].update({"extra": True}),
            "result keys",
        ),
        (
            lambda document: document["results"][0]["gate_decision"].update(
                {"extra": True}
            ),
            "gate decision keys",
        ),
        (
            lambda document: document["results"][0][
                "ingestion_result"
            ].update({"extra": True}),
            "ingestion result keys",
        ),
    ],
)
def test_store_schema_is_strict(tmp_path, mutation, message) -> None:
    path = tmp_path / "strict.json"
    JsonRecoveryGatedRunStore(path).append(_result("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    mutation(document)
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        JsonRecoveryGatedRunStore(path)


def test_nested_tampering_is_detected_by_collection_hash(tmp_path) -> None:
    path = tmp_path / "tampered.json"
    JsonRecoveryGatedRunStore(path).append(_result("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["results"][0]["gate_decision"]["manifest_count"] = 2
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        JsonRecoveryGatedRunStore(path)


def test_forged_nested_receipt_is_rejected_with_recomputed_hash(
    tmp_path,
) -> None:
    path = tmp_path / "forged.json"
    store = JsonRecoveryGatedRunStore(path)
    store.append(_result("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    gate = document["results"][0]["gate_decision"]
    gate["status"] = AuditRecoveryGateStatus.BLOCKED_ROLLBACK.value
    document["content_hash"] = store._compute_content_hash(
        document["results"]
    )
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid recovery-gated"):
        JsonRecoveryGatedRunStore(path)


def test_duplicate_identity_in_file_is_rejected(tmp_path) -> None:
    path = tmp_path / "duplicate.json"
    store = JsonRecoveryGatedRunStore(path)
    store.append(_result("a"))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["results"].append(document["results"][0])
    document["content_hash"] = store._compute_content_hash(
        document["results"]
    )
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate recovery-gated"):
        JsonRecoveryGatedRunStore(path)


def test_valid_orphaned_temporary_store_is_recovered(tmp_path) -> None:
    path = tmp_path / "recoverable.json"
    temporary_path = tmp_path / "recoverable.json.tmp"
    result = _result("a")
    JsonRecoveryGatedRunStore(path).append(result)
    path.replace(temporary_path)

    restored = JsonRecoveryGatedRunStore(path)

    assert restored.get(result.run_id) == result
    assert path.is_file()
    assert not temporary_path.exists()


def test_invalid_orphaned_temporary_store_is_retained(tmp_path) -> None:
    path = tmp_path / "invalid.json"
    temporary_path = tmp_path / "invalid.json.tmp"
    temporary_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ValueError, match="temporary recovery-gated"):
        JsonRecoveryGatedRunStore(path)

    assert not path.exists()
    assert temporary_path.is_file()


def test_primary_store_remains_authoritative(tmp_path) -> None:
    path = tmp_path / "authoritative.json"
    temporary_path = tmp_path / "authoritative.json.tmp"
    primary = _result("a")
    JsonRecoveryGatedRunStore(path).append(primary)
    primary_bytes = path.read_bytes()
    temporary_path.write_text("{not-json", encoding="utf-8")

    restored = JsonRecoveryGatedRunStore(path)

    assert tuple(restored.iter_results()) == (primary,)
    assert path.read_bytes() == primary_bytes
    assert temporary_path.is_file()


def test_failed_append_does_not_mutate_in_memory_state(tmp_path) -> None:
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("blocked", encoding="utf-8")
    store = JsonRecoveryGatedRunStore(blocked_parent / "runs.json")

    with pytest.raises(OSError):
        store.append(_result("a"))

    assert store.result_count == 0


def test_append_rejects_non_result(tmp_path) -> None:
    store = JsonRecoveryGatedRunStore(tmp_path / "runs.json")

    with pytest.raises(TypeError, match="RecoveryGatedIngestionResult"):
        store.append(object())  # type: ignore[arg-type]
