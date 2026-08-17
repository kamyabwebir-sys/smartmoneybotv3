from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from smart_money.adapters.persistence.json_ledger import (
    EvidenceGroundingLedger,
)
from smart_money.application.commit_receipt_verification import (
    CommitReceiptVerification,
    CommitReceiptVerificationError,
    revalidate_commit_receipt,
    verify_commit_receipt_or_raise,
)
from smart_money.application.durable_ingestion_commit import (
    DurableIngestionCommitReceipt,
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
    MarketStateChangeType,
    MarketStateCheckpoint,
    MarketStateCursor,
    make_market_state_change,
    make_market_state_checkpoint,
)
from smart_money.ingestion.contracts import EvidencePayload


class _CheckpointStore:
    def __init__(self, checkpoint: MarketStateCheckpoint | None) -> None:
        self.checkpoint = checkpoint

    def load(self) -> MarketStateCheckpoint:
        if self.checkpoint is None:
            raise FileNotFoundError("missing checkpoint")
        return self.checkpoint

    def save(self, checkpoint: MarketStateCheckpoint) -> None:
        self.checkpoint = checkpoint


def _committed_state():
    chain = ChainId("eip155", "8453")
    base = AssetId("WETH", chain, f"0x{'a' * 40}")
    quote = AssetId("USDC", chain, f"0x{'b' * 40}")
    market = MarketId(VenueId("uniswap-v3"), PairId(base, quote))
    change = make_market_state_change(
        source_id="evm.shadow.v3",
        source_event_id=f"0x{'c' * 64}:7",
        chain=chain,
        market=market,
        change_type=MarketStateChangeType.SWAP,
        occurred_at=1_700_000_100,
        chain_sequence=100,
        event_index=7,
        base_delta="-1",
        quote_delta="100",
    )
    evidence = make_canonical_market_state_observation(change)
    ledger = EvidenceGroundingLedger()
    ledger.append(evidence)
    cursor = MarketStateCursor(
        provider_id=change.source_id,
        chain=chain,
        chain_sequence=change.chain_sequence,
        event_index=change.event_index,
    )
    checkpoint = make_market_state_checkpoint(
        provider_id=change.source_id,
        chain=chain,
        market=market,
        cursor=cursor,
        reorder_window_blocks=2,
    )
    payload: dict[str, str | int] = {
        "accepted_count": 1,
        "checkpoint_id": checkpoint.checkpoint_id,
        "event_id": change.event_id,
        "evidence_id": evidence.get_canonical_id(),
        "ledger_content_hash": ledger.content_hash,
        "market_id": market.canonical_id,
        "provider_id": change.source_id,
        "schema_version": "durable_ingestion_commit.v1",
        "session_id": "session-1",
        "source_event_id": change.source_event_id,
    }
    receipt = DurableIngestionCommitReceipt(
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
    return receipt, change, ledger, checkpoint


def test_matching_state_produces_stable_immutable_verification() -> None:
    receipt, _, ledger, checkpoint = _committed_state()
    store = _CheckpointStore(checkpoint)

    first = revalidate_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=store,
    )
    second = verify_commit_receipt_or_raise(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=store,
    )

    assert first == second
    assert first.valid is True
    assert first.mismatch_fields == ()
    assert first.current_ledger_hash == ledger.content_hash
    assert first.persisted_checkpoint_id == checkpoint.checkpoint_id
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.valid = False  # type: ignore[misc]


def test_ledger_drift_and_missing_evidence_are_reported() -> None:
    receipt, _, ledger, checkpoint = _committed_state()
    ledger.append(
        EvidencePayload(
            source_id="other.provider",
            evidence_type="generic",
            timestamp=1,
            data={"value": 1},
        )
    )
    drift = revalidate_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=_CheckpointStore(checkpoint),
    )
    empty_ledger = EvidenceGroundingLedger()
    missing = revalidate_commit_receipt(
        receipt=receipt,
        ledger=empty_ledger,
        checkpoint_store=_CheckpointStore(checkpoint),
    )

    assert drift.mismatch_fields == ("ledger_content_hash",)
    assert missing.mismatch_fields == (
        "ledger_content_hash",
        "evidence_missing",
    )


def test_evidence_provenance_mismatch_is_reported_deterministically() -> None:
    receipt, _, _, checkpoint = _committed_state()
    mismatched = EvidencePayload(
        source_id="wrong.provider",
        evidence_type="generic",
        timestamp=1,
        data={
            "market_state_change": {
                "event_id": "wrong-event",
                "source_event_id": "wrong-source-event",
                "chain_sequence": 99,
                "event_index": 1,
            }
        },
        metadata={"provenance": {"market_id": "wrong-market"}},
    )
    ledger = EvidenceGroundingLedger()
    evidence_id = ledger.append(mismatched)
    payload = {
        **receipt.identity_payload(),
        "evidence_id": evidence_id,
        "ledger_content_hash": ledger.content_hash,
    }
    mismatched_receipt = DurableIngestionCommitReceipt(
        receipt_id=deterministic_id("durable_ingestion_commit", payload),
        session_id=receipt.session_id,
        provider_id=receipt.provider_id,
        market_id=receipt.market_id,
        event_id=receipt.event_id,
        source_event_id=receipt.source_event_id,
        evidence_id=evidence_id,
        ledger_content_hash=ledger.content_hash,
        checkpoint_id=receipt.checkpoint_id,
        accepted_count=receipt.accepted_count,
    )

    verification = revalidate_commit_receipt(
        receipt=mismatched_receipt,
        ledger=ledger,
        checkpoint_store=_CheckpointStore(checkpoint),
    )

    assert verification.mismatch_fields == (
        "evidence_type",
        "evidence_event_id",
        "evidence_source_event_id",
        "evidence_provider_id",
        "evidence_market_id",
        "checkpoint_cursor",
    )


def test_checkpoint_drift_and_missing_checkpoint_are_reported() -> None:
    receipt, change, ledger, checkpoint = _committed_state()
    later_cursor = MarketStateCursor(
        provider_id=checkpoint.provider_id,
        chain=checkpoint.chain,
        chain_sequence=change.chain_sequence + 1,
        event_index=0,
    )
    later_checkpoint = make_market_state_checkpoint(
        provider_id=checkpoint.provider_id,
        chain=checkpoint.chain,
        market=checkpoint.market,
        cursor=later_cursor,
        reorder_window_blocks=checkpoint.reorder_window_blocks,
    )

    drift = revalidate_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=_CheckpointStore(later_checkpoint),
    )
    missing = revalidate_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=_CheckpointStore(None),
    )

    assert drift.mismatch_fields == ("checkpoint_id", "checkpoint_cursor")
    assert drift.persisted_checkpoint_id == later_checkpoint.checkpoint_id
    assert missing.mismatch_fields == ("checkpoint_missing",)
    assert missing.persisted_checkpoint_id is None


def test_strict_verification_raises_with_same_deterministic_result() -> None:
    receipt, _, ledger, _ = _committed_state()
    store = _CheckpointStore(None)
    comparison = revalidate_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=store,
    )

    with pytest.raises(CommitReceiptVerificationError) as caught:
        verify_commit_receipt_or_raise(
            receipt=receipt,
            ledger=ledger,
            checkpoint_store=store,
        )

    assert caught.value.verification == comparison


def test_verification_constructor_rejects_forged_identity() -> None:
    receipt, _, ledger, checkpoint = _committed_state()
    verification = revalidate_commit_receipt(
        receipt=receipt,
        ledger=ledger,
        checkpoint_store=_CheckpointStore(checkpoint),
    )

    with pytest.raises(ValueError, match="verification_id"):
        CommitReceiptVerification(
            **{
                **verification.canonical_dict(),
                "verification_id": "forged",
            }
        )
