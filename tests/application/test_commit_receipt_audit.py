from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from smart_money.adapters.persistence.commit_receipt_store import (
    JsonCommitReceiptStore,
)
from smart_money.adapters.persistence.json_ledger import (
    EvidenceGroundingLedger,
)
from smart_money.application.commit_receipt_audit import (
    CommitReceiptAuditError,
    CommitReceiptAuditManifest,
    audit_commit_receipts,
    audit_commit_receipts_or_raise,
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


class _CheckpointStore:
    def __init__(self, checkpoint: MarketStateCheckpoint | None) -> None:
        self.checkpoint = checkpoint

    def load(self) -> MarketStateCheckpoint:
        if self.checkpoint is None:
            raise FileNotFoundError("missing checkpoint")
        return self.checkpoint

    def save(self, checkpoint: MarketStateCheckpoint) -> None:
        self.checkpoint = checkpoint


def _binding():
    chain = ChainId("eip155", "8453")
    base = AssetId("WETH", chain, f"0x{'a' * 40}")
    quote = AssetId("USDC", chain, f"0x{'b' * 40}")
    market = MarketId(VenueId("uniswap-v3"), PairId(base, quote))
    return chain, market


def _change(marker: str, sequence: int):
    chain, market = _binding()
    return make_market_state_change(
        source_id="evm.shadow.v3",
        source_event_id=f"0x{marker * 64}:{sequence}",
        chain=chain,
        market=market,
        change_type=MarketStateChangeType.SWAP,
        occurred_at=1_700_000_000 + sequence,
        chain_sequence=sequence,
        event_index=0,
        base_delta="-1",
        quote_delta="100",
    )


def _checkpoint(change) -> MarketStateCheckpoint:
    chain, market = _binding()
    return make_market_state_checkpoint(
        provider_id=change.source_id,
        chain=chain,
        market=market,
        cursor=MarketStateCursor(
            provider_id=change.source_id,
            chain=chain,
            chain_sequence=change.chain_sequence,
            event_index=change.event_index,
        ),
        reorder_window_blocks=2,
    )


def _receipt(
    change,
    ledger: EvidenceGroundingLedger,
    checkpoint: MarketStateCheckpoint,
    session_id: str,
) -> DurableIngestionCommitReceipt:
    evidence = make_canonical_market_state_observation(change)
    evidence_id = ledger.append(evidence)
    payload: dict[str, str | int] = {
        "accepted_count": 1,
        "checkpoint_id": checkpoint.checkpoint_id,
        "event_id": change.event_id,
        "evidence_id": evidence_id,
        "ledger_content_hash": ledger.content_hash,
        "market_id": change.market.canonical_id,
        "provider_id": change.source_id,
        "schema_version": "durable_ingestion_commit.v1",
        "session_id": session_id,
        "source_event_id": change.source_event_id,
    }
    return DurableIngestionCommitReceipt(
        receipt_id=deterministic_id("durable_ingestion_commit", payload),
        session_id=session_id,
        provider_id=change.source_id,
        market_id=change.market.canonical_id,
        event_id=change.event_id,
        source_event_id=change.source_event_id,
        evidence_id=evidence_id,
        ledger_content_hash=ledger.content_hash,
        checkpoint_id=checkpoint.checkpoint_id,
        accepted_count=1,
    )


def test_audit_mixed_history_is_deterministic_and_immutable(tmp_path) -> None:
    ledger = EvidenceGroundingLedger()
    first_change = _change("c", 100)
    first_checkpoint = _checkpoint(first_change)
    first_receipt = _receipt(
        first_change,
        ledger,
        first_checkpoint,
        "session-1",
    )
    second_change = _change("d", 101)
    second_checkpoint = _checkpoint(second_change)
    second_receipt = _receipt(
        second_change,
        ledger,
        second_checkpoint,
        "session-2",
    )
    receipt_store = JsonCommitReceiptStore(tmp_path / "receipts.json")
    receipt_store.append(first_receipt)
    receipt_store.append(second_receipt)
    checkpoint_store = _CheckpointStore(second_checkpoint)

    first = audit_commit_receipts(
        receipt_store=receipt_store,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )
    second = audit_commit_receipts(
        receipt_store=receipt_store,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )

    assert first == second
    assert first.receipt_store_hash == receipt_store.content_hash
    assert first.ledger_content_hash == ledger.content_hash
    assert first.receipt_count == 2
    assert first.valid_count == 1
    assert first.invalid_count == 1
    assert len(first.verification_ids) == 2
    assert first.invalid_receipt_ids == (first_receipt.receipt_id,)
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.invalid_count = 0  # type: ignore[misc]


def test_empty_receipt_store_produces_valid_empty_audit(tmp_path) -> None:
    receipt_store = JsonCommitReceiptStore(tmp_path / "empty.json")
    ledger = EvidenceGroundingLedger()

    manifest = audit_commit_receipts_or_raise(
        receipt_store=receipt_store,
        ledger=ledger,
        checkpoint_store=_CheckpointStore(None),
    )

    assert manifest.receipt_count == 0
    assert manifest.valid_count == 0
    assert manifest.invalid_count == 0
    assert manifest.verification_ids == ()
    assert manifest.invalid_receipt_ids == ()


def test_strict_audit_raises_with_same_manifest(tmp_path) -> None:
    ledger = EvidenceGroundingLedger()
    change = _change("c", 100)
    checkpoint = _checkpoint(change)
    receipt = _receipt(change, ledger, checkpoint, "session-1")
    receipt_store = JsonCommitReceiptStore(tmp_path / "receipts.json")
    receipt_store.append(receipt)
    ledger.append(
        make_canonical_market_state_observation(_change("d", 101))
    )
    checkpoint_store = _CheckpointStore(checkpoint)
    manifest = audit_commit_receipts(
        receipt_store=receipt_store,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )

    with pytest.raises(CommitReceiptAuditError) as caught:
        audit_commit_receipts_or_raise(
            receipt_store=receipt_store,
            ledger=ledger,
            checkpoint_store=checkpoint_store,
        )

    assert caught.value.manifest == manifest
    assert manifest.invalid_receipt_ids == (receipt.receipt_id,)


def test_audit_manifest_rejects_forged_identity(tmp_path) -> None:
    manifest = audit_commit_receipts(
        receipt_store=JsonCommitReceiptStore(tmp_path / "empty.json"),
        ledger=EvidenceGroundingLedger(),
        checkpoint_store=_CheckpointStore(None),
    )

    with pytest.raises(ValueError, match="audit_id"):
        CommitReceiptAuditManifest(
            **{
                **manifest.canonical_dict(),
                "audit_id": "forged",
            }
        )
