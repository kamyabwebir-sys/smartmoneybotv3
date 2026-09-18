from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from smart_money.adapters.persistence.historical_audit_manifest_store import (
    JsonHistoricalAuditManifestStore,
    JsonTrustedAuditHeadStore,
)
from smart_money.application.audit_recovery_gate import (
    AuditRecoveryGateBlockedError,
    AuditRecoveryGateStatus,
    FailClosedAuditRecoveryGate,
)
from smart_money.application.checkpointed_ingestion import (
    CheckpointedIngestionResult,
)
from smart_money.application.historical_receipt_audit import (
    HistoricalReceiptAuditManifest,
)
from smart_money.application.recovery_gated_ingestion import (
    CheckpointedIngestionRunner,
    RecoveryGatedIngestionResult,
    RecoveryGatedIngestionSession,
)
from smart_money.application.trusted_audit_head import (
    advance_trusted_audit_head,
    make_trusted_audit_head,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
)


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


def _market() -> MarketId:
    chain = ChainId("eip155", "8453")
    base = AssetId("WETH", chain, f"0x{'a' * 40}")
    quote = AssetId("USDC", chain, f"0x{'b' * 40}")
    return MarketId(VenueId("uniswap-v3"), PairId(base, quote))


def _ingestion_result(market: MarketId) -> CheckpointedIngestionResult:
    payload: dict[str, object] = {
        "accepted_count": 0,
        "final_checkpoint_id": None,
        "first_accepted_event_id": None,
        "last_accepted_event_id": None,
        "market_id": market.canonical_id,
        "provider_id": "evm.shadow.v3",
        "resumed_from_checkpoint_id": None,
        "schema_version": "checkpointed_ingestion_result.v1",
    }
    return CheckpointedIngestionResult(
        session_id=deterministic_id(
            "checkpointed_ingestion_result",
            payload,
        ),
        provider_id="evm.shadow.v3",
        market_id=market.canonical_id,
        resumed_from_checkpoint_id=None,
        first_accepted_event_id=None,
        last_accepted_event_id=None,
        accepted_count=0,
        final_checkpoint_id=None,
    )


class _SpySession:
    def __init__(self, result: CheckpointedIngestionResult) -> None:
        self.result = result
        self.calls: list[tuple[str, int | None]] = []
        self.error: Exception | None = None

    async def run(
        self,
        market: MarketId,
        *,
        max_events: int | None = None,
    ) -> CheckpointedIngestionResult:
        self.calls.append((market.canonical_id, max_events))
        if self.error is not None:
            raise self.error
        return self.result


def _system(tmp_path):
    manifests = JsonHistoricalAuditManifestStore(
        tmp_path / "historical-audits.json"
    )
    heads = JsonTrustedAuditHeadStore(tmp_path / "trusted-head.json")
    gate = FailClosedAuditRecoveryGate(manifests, heads)
    market = _market()
    session = _SpySession(_ingestion_result(market))
    wrapper = RecoveryGatedIngestionSession(gate, session)
    return manifests, heads, market, session, wrapper


@pytest.mark.asyncio
async def test_missing_head_blocks_before_ingestion_session(tmp_path) -> None:
    manifests, heads, market, session, wrapper = _system(tmp_path)
    manifests.append(_manifest("a"))

    with pytest.raises(AuditRecoveryGateBlockedError):
        await wrapper.run(market)

    assert isinstance(session, CheckpointedIngestionRunner)
    assert session.calls == []
    assert not heads.file_path.exists()


@pytest.mark.asyncio
async def test_explicit_bootstrap_links_gate_and_ingestion_deterministically(
    tmp_path,
) -> None:
    manifests, heads, market, session, wrapper = _system(tmp_path)
    manifests.append(_manifest("a"))

    advanced = await wrapper.run(
        market,
        max_events=2,
        advance_if_required=True,
    )
    current_first = await wrapper.run(market, max_events=2)
    head_bytes = heads.file_path.read_bytes()
    current_second = await wrapper.run(market, max_events=2)
    current_other_limit = await wrapper.run(market, max_events=1)

    assert advanced.gate_decision.status is (
        AuditRecoveryGateStatus.READY_ADVANCED
    )
    assert current_first.gate_decision.status is (
        AuditRecoveryGateStatus.READY_CURRENT
    )
    assert current_first == current_second
    assert current_other_limit != current_first
    assert current_other_limit.requested_max_events == 1
    assert advanced.gate_decision_id == advanced.gate_decision.decision_id
    assert (
        advanced.ingestion_session_id
        == advanced.ingestion_result.session_id
    )
    assert session.calls == [
        (market.canonical_id, 2),
        (market.canonical_id, 2),
        (market.canonical_id, 2),
        (market.canonical_id, 1),
    ]
    assert heads.file_path.read_bytes() == head_bytes


@pytest.mark.asyncio
async def test_new_manifest_requires_explicit_head_advance(tmp_path) -> None:
    manifests, heads, market, session, wrapper = _system(tmp_path)
    manifests.append(_manifest("a"))
    first_head = advance_trusted_audit_head(
        manifest_store=manifests,
        head_store=heads,
    )
    manifests.append(_manifest("b"))

    with pytest.raises(AuditRecoveryGateBlockedError):
        await wrapper.run(market)
    advanced = await wrapper.run(
        market,
        advance_if_required=True,
    )

    assert len(session.calls) == 1
    assert advanced.gate_decision.status is (
        AuditRecoveryGateStatus.READY_ADVANCED
    )
    assert heads.load().previous_anchor_id == first_head.anchor_id


@pytest.mark.asyncio
async def test_rollback_blocks_session_even_when_advance_requested(
    tmp_path,
) -> None:
    source = JsonHistoricalAuditManifestStore(tmp_path / "source.json")
    source.append(_manifest("a"))
    source.append(_manifest("b"))
    trusted_head = make_trusted_audit_head(manifest_store=source)

    rollback = JsonHistoricalAuditManifestStore(tmp_path / "rollback.json")
    rollback.append(_manifest("a"))
    heads = JsonTrustedAuditHeadStore(tmp_path / "trusted-head.json")
    heads.save(trusted_head)
    market = _market()
    session = _SpySession(_ingestion_result(market))
    wrapper = RecoveryGatedIngestionSession(
        FailClosedAuditRecoveryGate(rollback, heads),
        session,
    )

    with pytest.raises(AuditRecoveryGateBlockedError) as caught:
        await wrapper.run(
            market,
            advance_if_required=True,
        )

    assert caught.value.decision.status is (
        AuditRecoveryGateStatus.BLOCKED_ROLLBACK
    )
    assert session.calls == []


@pytest.mark.asyncio
async def test_invalid_request_is_rejected_before_head_advance(tmp_path) -> None:
    manifests, heads, _, session, wrapper = _system(tmp_path)
    manifests.append(_manifest("a"))

    with pytest.raises(TypeError, match="MarketId"):
        await wrapper.run(  # type: ignore[arg-type]
            "not-a-market",
            advance_if_required=True,
        )
    with pytest.raises(ValueError, match="positive"):
        await wrapper.run(
            _market(),
            max_events=0,
            advance_if_required=True,
        )

    assert session.calls == []
    assert not heads.file_path.exists()


@pytest.mark.asyncio
async def test_session_failure_propagates_without_result(tmp_path) -> None:
    manifests, heads, market, session, wrapper = _system(tmp_path)
    manifests.append(_manifest("a"))
    session.error = RuntimeError("ingestion failed")

    with pytest.raises(RuntimeError, match="ingestion failed"):
        await wrapper.run(
            market,
            advance_if_required=True,
        )

    assert len(session.calls) == 1
    assert heads.file_path.is_file()


def test_result_is_immutable_and_rejects_forged_identity(tmp_path) -> None:
    manifests, _, _, _, wrapper = _system(tmp_path)
    manifests.append(_manifest("a"))
    decision = wrapper.gate.evaluate()
    assert decision.allowed is False

    with pytest.raises(ValueError, match="authorize"):
        RecoveryGatedIngestionResult(
            run_id="forged",
            gate_decision=decision,
            ingestion_result=_ingestion_result(_market()),
            requested_max_events=None,
        )

    allowed_decision = wrapper.gate.evaluate(advance_if_required=True)
    ingestion_result = _ingestion_result(_market())
    payload = {
        "gate_decision": allowed_decision.canonical_dict(),
        "ingestion_result": ingestion_result.canonical_dict(),
        "requested_max_events": None,
        "schema_version": "recovery_gated_ingestion.v1",
    }
    result = RecoveryGatedIngestionResult(
        run_id=deterministic_id("recovery_gated_ingestion", payload),
        gate_decision=allowed_decision,
        ingestion_result=ingestion_result,
        requested_max_events=None,
    )

    assert not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        result.run_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="run_id"):
        RecoveryGatedIngestionResult(
            **{
                **result.canonical_dict(),
                "run_id": "forged",
                "gate_decision": result.gate_decision,
                "ingestion_result": result.ingestion_result,
                "requested_max_events": result.requested_max_events,
            }
        )
