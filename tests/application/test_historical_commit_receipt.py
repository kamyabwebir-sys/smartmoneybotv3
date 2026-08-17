from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from smart_money.adapters.persistence.durable_json_ledger import (
    DurableJsonEvidenceLedger,
)
from smart_money.application.durable_ingestion_commit import (
    DurableIngestionCommitReceipt,
)
from smart_money.application.historical_commit_receipt import (
    HistoricalCommitAssessment,
    HistoricalCommitAssessmentError,
    HistoricalCommitStatus,
    assess_historical_commit_receipt,
    verify_historical_commit_receipt_or_raise,
)
from smart_money.application.market_state_observation_consumer import (
    make_canonical_market_state_observation,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.market_identity import (
    AssetId,
    ChainId,
    MarketId,
    PairId,
    VenueId,
)
from smart_money.domain.market_state import (
    MarketStateChange,
    MarketStateChangeType,
    MarketStateCheckpoint,
    MarketStateCursor,
    make_market_state_change,
    make_market_state_checkpoint,
)


class _CheckpointStore:
    def __init__(self, checkpoint: MarketStateCheckpoint | None) -> None:
        self.checkpoint = checkpoint

    def load(self) -> MarketStateCheckpoint:
        if self.checkpoint is None:
            raise FileNotFoundError("missing checkpoint")
        return self.checkpoint

    def save(self, checkpoint: MarketStateCheckpoint) -> None:
        self.checkpoint = checkpoint


def _market() -> tuple[ChainId, MarketId]:
    chain = ChainId("eip155", "8453")
    base = AssetId("WETH", chain, f"0x{'a' * 40}")
    quote = AssetId("USDC", chain, f"0x{'b' * 40}")
    return chain, MarketId(VenueId("uniswap-v3"), PairId(base, quote))


def _change(
    chain: ChainId,
    market: MarketId,
    *,
    sequence: int,
) -> MarketStateChange:
    return make_market_state_change(
        source_id="evm.shadow.v3",
        source_event_id=f"0x{sequence:064x}:0",
        chain=chain,
        market=market,
        change_type=MarketStateChangeType.SWAP,
        occurred_at=1_700_000_000 + sequence,
        chain_sequence=sequence,
        event_index=0,
        base_delta="-1",
        quote_delta="100",
    )


def _checkpoint(change: MarketStateChange) -> MarketStateCheckpoint:
    return make_market_state_checkpoint(
        provider_id=change.source_id,
        chain=change.chain,
        market=change.market,
        cursor=MarketStateCursor(
            provider_id=change.source_id,
            chain=change.chain,
            chain_sequence=change.chain_sequence,
            event_index=change.event_index,
        ),
        reorder_window_blocks=2,
    )


def _receipt(
    change: MarketStateChange,
    ledger: DurableJsonEvidenceLedger,
    checkpoint: MarketStateCheckpoint,
    *,
    ledger_hash: str | None = None,
) -> DurableIngestionCommitReceipt:
    evidence_id = make_canonical_market_state_observation(
        change
    ).get_canonical_id()
    payload: dict[str, str | int] = {
        "accepted_count": 1,
        "checkpoint_id": checkpoint.checkpoint_id,
        "event_id": change.event_id,
        "evidence_id": evidence_id,
        "ledger_content_hash": ledger_hash or ledger.content_hash,
        "market_id": change.market.canonical_id,
        "provider_id": change.source_id,
        "schema_version": "durable_ingestion_commit.v1",
        "session_id": f"session-{change.chain_sequence}",
        "source_event_id": change.source_event_id,
    }
    return DurableIngestionCommitReceipt(
        receipt_id=deterministic_id("durable_ingestion_commit", payload),
        session_id=payload["session_id"],
        provider_id=payload["provider_id"],
        market_id=payload["market_id"],
        event_id=payload["event_id"],
        source_event_id=payload["source_event_id"],
        evidence_id=payload["evidence_id"],
        ledger_content_hash=payload["ledger_content_hash"],
        checkpoint_id=payload["checkpoint_id"],
        accepted_count=1,
    )


def _append(
    ledger: DurableJsonEvidenceLedger,
    change: MarketStateChange,
) -> None:
    ledger.append(make_canonical_market_state_observation(change))


def test_current_and_historical_receipts_are_distinguished(tmp_path) -> None:
    chain, market = _market()
    first = _change(chain, market, sequence=100)
    second = _change(chain, market, sequence=101)
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")
    _append(ledger, first)
    first_receipt = _receipt(first, ledger, _checkpoint(first))
    _append(ledger, second)
    second_checkpoint = _checkpoint(second)
    second_receipt = _receipt(second, ledger, second_checkpoint)
    store = _CheckpointStore(second_checkpoint)

    historical = assess_historical_commit_receipt(
        receipt=first_receipt,
        ledger=ledger,
        checkpoint_store=store,
    )
    current = verify_historical_commit_receipt_or_raise(
        receipt=second_receipt,
        ledger=ledger,
        checkpoint_store=store,
    )

    assert historical.status is HistoricalCommitStatus.HISTORICALLY_VALID
    assert historical.reason_codes == ("historical_anchors_match",)
    assert historical.ledger_anchor_found is True
    assert historical.checkpoint_anchor_matches is True
    assert current.status is HistoricalCommitStatus.CURRENT


def test_one_sided_advancement_is_reported_as_drift(tmp_path) -> None:
    chain, market = _market()
    first = _change(chain, market, sequence=100)
    second = _change(chain, market, sequence=101)
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")
    _append(ledger, first)
    checkpoint = _checkpoint(first)
    receipt = _receipt(first, ledger, checkpoint)
    _append(ledger, second)

    assessment = assess_historical_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=_CheckpointStore(checkpoint),
    )

    assert assessment.status is HistoricalCommitStatus.DRIFTED
    assert assessment.reason_codes == ("ledger_checkpoint_drift",)
    with pytest.raises(HistoricalCommitAssessmentError) as caught:
        verify_historical_commit_receipt_or_raise(
            receipt=receipt,
            ledger=ledger,
            checkpoint_store=_CheckpointStore(checkpoint),
        )
    assert caught.value.assessment == assessment


def test_missing_evidence_or_checkpoint_fails_closed(tmp_path) -> None:
    chain, market = _market()
    change = _change(chain, market, sequence=100)
    populated = DurableJsonEvidenceLedger(tmp_path / "populated.json")
    _append(populated, change)
    checkpoint = _checkpoint(change)
    receipt = _receipt(change, populated, checkpoint)
    empty = DurableJsonEvidenceLedger(tmp_path / "empty.json")

    missing_evidence = assess_historical_commit_receipt(
        receipt=receipt,
        ledger=empty,
        checkpoint_store=_CheckpointStore(checkpoint),
    )
    missing_checkpoint = assess_historical_commit_receipt(
        receipt=receipt,
        ledger=populated,
        checkpoint_store=_CheckpointStore(None),
    )

    assert missing_evidence.status is HistoricalCommitStatus.MISSING
    assert missing_evidence.reason_codes == ("evidence_missing",)
    assert missing_checkpoint.status is HistoricalCommitStatus.MISSING
    assert missing_checkpoint.reason_codes == ("checkpoint_missing",)


def test_unknown_ledger_prefix_is_corrupted(tmp_path) -> None:
    chain, market = _market()
    change = _change(chain, market, sequence=100)
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")
    _append(ledger, change)
    checkpoint = _checkpoint(change)
    receipt = _receipt(
        change,
        ledger,
        checkpoint,
        ledger_hash="f" * 64,
    )

    assessment = assess_historical_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=_CheckpointStore(checkpoint),
    )

    assert assessment.status is HistoricalCommitStatus.CORRUPTED
    assert assessment.reason_codes == ("ledger_prefix_missing",)
    assert assessment.ledger_anchor_found is False


def test_checkpoint_rollback_and_binding_conflict_are_distinct(tmp_path) -> None:
    chain, market = _market()
    first = _change(chain, market, sequence=100)
    second = _change(chain, market, sequence=101)
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")
    _append(ledger, first)
    _append(ledger, second)
    receipt = _receipt(second, ledger, _checkpoint(second))

    rollback = assess_historical_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=_CheckpointStore(_checkpoint(first)),
    )
    other_market = MarketId(
        VenueId("aerodrome"),
        market.pair,
    )
    conflicting = make_market_state_checkpoint(
        provider_id=second.source_id,
        chain=chain,
        market=other_market,
        cursor=MarketStateCursor(
            provider_id=second.source_id,
            chain=chain,
            chain_sequence=second.chain_sequence,
            event_index=second.event_index,
        ),
        reorder_window_blocks=2,
    )
    conflict = assess_historical_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=_CheckpointStore(conflicting),
    )

    assert rollback.status is HistoricalCommitStatus.CONFLICT
    assert rollback.reason_codes == ("current_cursor_behind",)
    assert conflict.status is HistoricalCommitStatus.CONFLICT
    assert conflict.reason_codes == ("checkpoint_binding_conflict",)


def test_prefix_lookup_validates_hash_and_survives_reload(tmp_path) -> None:
    chain, market = _market()
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")
    _append(ledger, _change(chain, market, sequence=100))
    historical_hash = ledger.content_hash
    _append(ledger, _change(chain, market, sequence=101))

    restored = DurableJsonEvidenceLedger(ledger.file_path)

    assert restored.contains_content_hash(historical_hash) is True
    assert restored.contains_content_hash("0" * 64) is False
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        restored.contains_content_hash("invalid")


def test_assessment_is_immutable_and_rejects_forged_identity(tmp_path) -> None:
    chain, market = _market()
    change = _change(chain, market, sequence=100)
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")
    _append(ledger, change)
    checkpoint = _checkpoint(change)
    receipt = _receipt(change, ledger, checkpoint)
    assessment = assess_historical_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=_CheckpointStore(checkpoint),
    )

    assert not hasattr(assessment, "__dict__")
    with pytest.raises(FrozenInstanceError):
        assessment.status = HistoricalCommitStatus.DRIFTED  # type: ignore[misc]
    with pytest.raises(ValueError, match="assessment_id"):
        HistoricalCommitAssessment(
            **{
                **assessment.canonical_dict(),
                "assessment_id": "forged",
                "status": assessment.status,
            }
        )
