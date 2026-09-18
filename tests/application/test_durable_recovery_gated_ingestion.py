from __future__ import annotations

from dataclasses import FrozenInstanceError

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
from smart_money.application.durable_recovery_gated_ingestion import (
    DurableRecoveryGatedIngestionOrchestrator,
    DurableRecoveryGatedIngestionReceipt,
    RecoveryGatedIngestionRunner,
)
from smart_money.application.recovery_gated_ingestion import (
    RecoveryGatedIngestionResult,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
)


def _market(marker: str = "a") -> MarketId:
    chain = ChainId("eip155", "8453")
    base = AssetId("WETH", chain, f"0x{marker * 40}")
    quote = AssetId("USDC", chain, f"0x{'b' * 40}")
    return MarketId(VenueId("uniswap-v3"), PairId(base, quote))


def _result(market: MarketId) -> RecoveryGatedIngestionResult:
    gate_payload: dict[str, object] = {
        "advance_requested": False,
        "allowed": True,
        "latest_audit_id": "audit-a",
        "manifest_count": 1,
        "manifest_store_hash": "a" * 64,
        "schema_version": "audit_recovery_gate.v1",
        "status": AuditRecoveryGateStatus.READY_CURRENT.value,
        "trusted_anchor_id": "anchor-a",
        "verification_id": "verification-a",
    }
    gate = AuditRecoveryGateDecision(
        decision_id=deterministic_id("audit_recovery_gate", gate_payload),
        status=AuditRecoveryGateStatus.READY_CURRENT,
        allowed=True,
        advance_requested=False,
        trusted_anchor_id="anchor-a",
        verification_id="verification-a",
        manifest_store_hash="a" * 64,
        manifest_count=1,
        latest_audit_id="audit-a",
    )
    ingestion_payload: dict[str, object] = {
        "accepted_count": 0,
        "final_checkpoint_id": None,
        "first_accepted_event_id": None,
        "last_accepted_event_id": None,
        "market_id": market.canonical_id,
        "provider_id": "evm.shadow.v3",
        "resumed_from_checkpoint_id": None,
        "schema_version": "checkpointed_ingestion_result.v1",
    }
    ingestion = CheckpointedIngestionResult(
        session_id=deterministic_id(
            "checkpointed_ingestion_result",
            ingestion_payload,
        ),
        provider_id="evm.shadow.v3",
        market_id=market.canonical_id,
        resumed_from_checkpoint_id=None,
        first_accepted_event_id=None,
        last_accepted_event_id=None,
        accepted_count=0,
        final_checkpoint_id=None,
    )
    payload: dict[str, object] = {
        "gate_decision": gate.canonical_dict(),
        "ingestion_result": ingestion.canonical_dict(),
        "requested_max_events": 2,
        "schema_version": "recovery_gated_ingestion.v1",
    }
    return RecoveryGatedIngestionResult(
        run_id=deterministic_id("recovery_gated_ingestion", payload),
        gate_decision=gate,
        ingestion_result=ingestion,
        requested_max_events=2,
    )


class _SpyRunner:
    def __init__(self, result: object) -> None:
        self.result = result
        self.calls: list[tuple[str, int | None, bool]] = []
        self.error: Exception | None = None

    async def run(
        self,
        market: MarketId,
        *,
        max_events: int | None = None,
        advance_if_required: bool = False,
    ) -> RecoveryGatedIngestionResult:
        self.calls.append(
            (market.canonical_id, max_events, advance_if_required)
        )
        if self.error is not None:
            raise self.error
        return self.result  # type: ignore[return-value]


class _WrongAcknowledgementStore(JsonRecoveryGatedRunStore):
    def append(self, result: RecoveryGatedIngestionResult) -> str:
        super().append(result)
        return "wrong-run-id"


class _DiscardingStore(JsonRecoveryGatedRunStore):
    def get(self, run_id: str) -> RecoveryGatedIngestionResult | None:
        return None


@pytest.mark.asyncio
async def test_orchestrator_persists_and_links_exact_result(tmp_path) -> None:
    market = _market()
    result = _result(market)
    runner = _SpyRunner(result)
    store = JsonRecoveryGatedRunStore(tmp_path / "runs.json")
    orchestrator = DurableRecoveryGatedIngestionOrchestrator(runner, store)

    receipt = await orchestrator.run(
        market,
        max_events=2,
        advance_if_required=True,
    )

    assert isinstance(runner, RecoveryGatedIngestionRunner)
    assert receipt.result == result
    assert receipt.run_id == result.run_id
    assert receipt.gate_decision_id == result.gate_decision_id
    assert receipt.ingestion_session_id == result.ingestion_session_id
    assert receipt.run_store_content_hash == store.content_hash
    assert receipt.run_store_result_count == store.result_count == 1
    assert receipt.newly_persisted is True
    assert store.get(result.run_id) == result
    assert runner.calls == [(market.canonical_id, 2, True)]
    assert not hasattr(receipt, "__dict__")
    with pytest.raises(FrozenInstanceError):
        receipt.newly_persisted = False  # type: ignore[misc]


@pytest.mark.asyncio
async def test_duplicate_run_is_idempotent_and_byte_stable(tmp_path) -> None:
    market = _market()
    result = _result(market)
    store = JsonRecoveryGatedRunStore(tmp_path / "runs.json")
    orchestrator = DurableRecoveryGatedIngestionOrchestrator(
        _SpyRunner(result),
        store,
    )

    first = await orchestrator.run(market, max_events=2)
    first_bytes = store.file_path.read_bytes()
    second = await orchestrator.run(market, max_events=2)

    assert first.newly_persisted is True
    assert second.newly_persisted is False
    assert second.run_id == first.run_id
    assert second.run_store_content_hash == first.run_store_content_hash
    assert second.run_store_result_count == first.run_store_result_count == 1
    assert store.file_path.read_bytes() == first_bytes


@pytest.mark.asyncio
async def test_invalid_request_is_rejected_before_runner_or_store(
    tmp_path,
) -> None:
    market = _market()
    runner = _SpyRunner(_result(market))
    store = JsonRecoveryGatedRunStore(tmp_path / "runs.json")
    orchestrator = DurableRecoveryGatedIngestionOrchestrator(runner, store)

    with pytest.raises(TypeError, match="MarketId"):
        await orchestrator.run("invalid")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="positive"):
        await orchestrator.run(market, max_events=0)

    assert runner.calls == []
    assert store.result_count == 0
    assert not store.file_path.exists()


@pytest.mark.asyncio
async def test_runner_failure_leaves_result_store_unchanged(tmp_path) -> None:
    market = _market()
    runner = _SpyRunner(_result(market))
    runner.error = RuntimeError("ingestion failed")
    store = JsonRecoveryGatedRunStore(tmp_path / "runs.json")

    with pytest.raises(RuntimeError, match="ingestion failed"):
        await DurableRecoveryGatedIngestionOrchestrator(
            runner,
            store,
        ).run(market)

    assert store.result_count == 0
    assert not store.file_path.exists()


@pytest.mark.asyncio
async def test_persistence_failure_occurs_after_ingestion_without_receipt(
    tmp_path,
) -> None:
    market = _market()
    runner = _SpyRunner(_result(market))
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("blocked", encoding="utf-8")
    store = JsonRecoveryGatedRunStore(blocked_parent / "runs.json")

    with pytest.raises(OSError):
        await DurableRecoveryGatedIngestionOrchestrator(
            runner,
            store,
        ).run(market)

    assert len(runner.calls) == 1
    assert store.result_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("store_type", "message"),
    [
        (_WrongAcknowledgementStore, "acknowledgement"),
        (_DiscardingStore, "retain the exact"),
    ],
)
async def test_store_contract_violation_fails_closed(
    tmp_path,
    store_type,
    message,
) -> None:
    market = _market()
    result = _result(market)
    store = store_type(tmp_path / "runs.json")

    with pytest.raises(RuntimeError, match=message):
        await DurableRecoveryGatedIngestionOrchestrator(
            _SpyRunner(result),
            store,
        ).run(market)


@pytest.mark.asyncio
async def test_wrong_result_type_or_market_fails_before_persistence(
    tmp_path,
) -> None:
    market = _market()
    store = JsonRecoveryGatedRunStore(tmp_path / "runs.json")

    with pytest.raises(RuntimeError, match="invalid result type"):
        await DurableRecoveryGatedIngestionOrchestrator(
            _SpyRunner(object()),
            store,
        ).run(market)
    with pytest.raises(RuntimeError, match="market"):
        await DurableRecoveryGatedIngestionOrchestrator(
            _SpyRunner(_result(_market("c"))),
            store,
        ).run(market)

    assert store.result_count == 0


def test_receipt_rejects_forged_identity(tmp_path) -> None:
    market = _market()
    result = _result(market)
    store = JsonRecoveryGatedRunStore(tmp_path / "runs.json")
    store.append(result)
    payload: dict[str, object] = {
        "newly_persisted": True,
        "result": result.canonical_dict(),
        "run_store_content_hash": store.content_hash,
        "run_store_result_count": store.result_count,
        "schema_version": "durable_recovery_gated_ingestion.v1",
    }

    with pytest.raises(ValueError, match="receipt_id"):
        DurableRecoveryGatedIngestionReceipt(
            receipt_id="forged",
            result=result,
            run_store_content_hash=store.content_hash,
            run_store_result_count=store.result_count,
            newly_persisted=True,
        )
    receipt = DurableRecoveryGatedIngestionReceipt(
        receipt_id=deterministic_id(
            "durable_recovery_gated_ingestion",
            payload,
        ),
        result=result,
        run_store_content_hash=store.content_hash,
        run_store_result_count=store.result_count,
        newly_persisted=True,
    )
    assert receipt.canonical_dict() == {
        "receipt_id": receipt.receipt_id,
        **payload,
    }
