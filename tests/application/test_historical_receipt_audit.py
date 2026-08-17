from __future__ import annotations

from collections.abc import Iterator
from dataclasses import FrozenInstanceError

import pytest

from smart_money.adapters.persistence.commit_receipt_store import (
    JsonCommitReceiptStore,
)
from smart_money.adapters.persistence.durable_json_ledger import (
    DurableJsonEvidenceLedger,
)
from smart_money.application.durable_ingestion_commit import (
    DurableIngestionCommitReceipt,
)
from smart_money.application.historical_receipt_audit import (
    HistoricalReceiptAuditError,
    HistoricalReceiptAuditManifest,
    audit_historical_receipts,
    audit_historical_receipts_or_raise,
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


class _ChangingCheckpointStore:
    def __init__(
        self,
        first: MarketStateCheckpoint,
        second: MarketStateCheckpoint,
    ) -> None:
        self._values = iter((first, second))

    def load(self) -> MarketStateCheckpoint:
        return next(self._values)

    def save(self, checkpoint: MarketStateCheckpoint) -> None:
        raise RuntimeError("read-only test store")


class _MutatingLedger:
    def __init__(self, ledger: DurableJsonEvidenceLedger) -> None:
        self._ledger = ledger
        self._mutated = False

    def append(self, payload: EvidencePayload) -> str:
        return self._ledger.append(payload)

    def contains(self, canonical_id: str) -> bool:
        return self._ledger.contains(canonical_id)

    def get(self, canonical_id: str) -> EvidencePayload | None:
        if not self._mutated:
            self._mutated = True
            self._ledger.append(
                EvidencePayload(
                    source_id="concurrent.source",
                    timestamp=1,
                    data={"mutation": True},
                )
            )
        return self._ledger.get(canonical_id)

    def iter_payloads(self) -> Iterator[EvidencePayload]:
        return self._ledger.iter_payloads()

    def contains_content_hash(self, content_hash: str) -> bool:
        return self._ledger.contains_content_hash(content_hash)

    @property
    def entry_count(self) -> int:
        return self._ledger.entry_count

    @property
    def content_hash(self) -> str:
        return self._ledger.content_hash


def _market() -> tuple[ChainId, MarketId]:
    chain = ChainId("eip155", "8453")
    base = AssetId("WETH", chain, f"0x{'a' * 40}")
    quote = AssetId("USDC", chain, f"0x{'b' * 40}")
    return chain, MarketId(VenueId("uniswap-v3"), PairId(base, quote))


def _change(
    chain: ChainId,
    market: MarketId,
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


def _append_receipt(
    *,
    change: MarketStateChange,
    ledger: DurableJsonEvidenceLedger,
    receipt_store: JsonCommitReceiptStore,
) -> DurableIngestionCommitReceipt:
    evidence = make_canonical_market_state_observation(change)
    evidence_id = ledger.append(evidence)
    checkpoint = _checkpoint(change)
    payload: dict[str, str | int] = {
        "accepted_count": 1,
        "checkpoint_id": checkpoint.checkpoint_id,
        "event_id": change.event_id,
        "evidence_id": evidence_id,
        "ledger_content_hash": ledger.content_hash,
        "market_id": change.market.canonical_id,
        "provider_id": change.source_id,
        "schema_version": "durable_ingestion_commit.v1",
        "session_id": f"session-{change.chain_sequence}",
        "source_event_id": change.source_event_id,
    }
    receipt = DurableIngestionCommitReceipt(
        receipt_id=deterministic_id("durable_ingestion_commit", payload),
        session_id=payload["session_id"],
        provider_id=payload["provider_id"],
        market_id=payload["market_id"],
        event_id=payload["event_id"],
        source_event_id=payload["source_event_id"],
        evidence_id=evidence_id,
        ledger_content_hash=payload["ledger_content_hash"],
        checkpoint_id=checkpoint.checkpoint_id,
        accepted_count=1,
    )
    receipt_store.append(receipt)
    return receipt


def test_mixed_history_manifest_is_deterministic_and_immutable(tmp_path) -> None:
    chain, market = _market()
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")
    receipts = JsonCommitReceiptStore(tmp_path / "receipts.json")
    first = _append_receipt(
        change=_change(chain, market, 100),
        ledger=ledger,
        receipt_store=receipts,
    )
    second_change = _change(chain, market, 101)
    _append_receipt(
        change=second_change,
        ledger=ledger,
        receipt_store=receipts,
    )
    checkpoint_store = _CheckpointStore(_checkpoint(second_change))

    manifest = audit_historical_receipts_or_raise(
        receipt_store=receipts,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )
    repeated = audit_historical_receipts(
        receipt_store=receipts,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )

    assert manifest == repeated
    assert manifest.receipt_count == 2
    assert manifest.current_count == 1
    assert manifest.historically_valid_count == 1
    assert manifest.accepted_count == 2
    assert manifest.rejected_count == 0
    assert manifest.rejected_receipt_ids == ()
    assert len(manifest.assessment_ids) == 2
    assert first.receipt_id not in manifest.rejected_receipt_ids
    assert not hasattr(manifest, "__dict__")
    with pytest.raises(FrozenInstanceError):
        manifest.current_count = 0  # type: ignore[misc]


def test_drift_is_counted_and_strict_audit_rejects_it(tmp_path) -> None:
    chain, market = _market()
    first_change = _change(chain, market, 100)
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")
    receipts = JsonCommitReceiptStore(tmp_path / "receipts.json")
    receipt = _append_receipt(
        change=first_change,
        ledger=ledger,
        receipt_store=receipts,
    )
    ledger.append(
        make_canonical_market_state_observation(
            _change(chain, market, 101)
        )
    )
    checkpoint_store = _CheckpointStore(_checkpoint(first_change))

    manifest = audit_historical_receipts(
        receipt_store=receipts,
        ledger=ledger,
        checkpoint_store=checkpoint_store,
    )

    assert manifest.drifted_count == 1
    assert manifest.rejected_count == 1
    assert manifest.rejected_receipt_ids == (receipt.receipt_id,)
    with pytest.raises(HistoricalReceiptAuditError) as caught:
        audit_historical_receipts_or_raise(
            receipt_store=receipts,
            ledger=ledger,
            checkpoint_store=checkpoint_store,
        )
    assert caught.value.manifest == manifest


def test_empty_store_produces_empty_accepted_manifest(tmp_path) -> None:
    manifest = audit_historical_receipts_or_raise(
        receipt_store=JsonCommitReceiptStore(tmp_path / "receipts.json"),
        ledger=DurableJsonEvidenceLedger(tmp_path / "ledger.json"),
        checkpoint_store=_CheckpointStore(None),
    )

    assert manifest.receipt_count == 0
    assert manifest.accepted_count == 0
    assert manifest.rejected_count == 0
    assert manifest.assessment_ids == ()


def test_concurrent_ledger_and_checkpoint_changes_fail_closed(tmp_path) -> None:
    chain, market = _market()
    first_change = _change(chain, market, 100)
    second_change = _change(chain, market, 101)
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")
    receipts = JsonCommitReceiptStore(tmp_path / "receipts.json")
    _append_receipt(
        change=first_change,
        ledger=ledger,
        receipt_store=receipts,
    )

    with pytest.raises(RuntimeError, match="Ledger changed"):
        audit_historical_receipts(
            receipt_store=receipts,
            ledger=_MutatingLedger(ledger),
            checkpoint_store=_CheckpointStore(_checkpoint(first_change)),
        )

    stable_ledger = DurableJsonEvidenceLedger(tmp_path / "stable-ledger.json")
    stable_receipts = JsonCommitReceiptStore(
        tmp_path / "stable-receipts.json"
    )
    _append_receipt(
        change=first_change,
        ledger=stable_ledger,
        receipt_store=stable_receipts,
    )
    with pytest.raises(RuntimeError, match="checkpoint changed"):
        audit_historical_receipts(
            receipt_store=stable_receipts,
            ledger=stable_ledger,
            checkpoint_store=_ChangingCheckpointStore(
                _checkpoint(first_change),
                _checkpoint(second_change),
            ),
        )


def test_manifest_rejects_forged_identity(tmp_path) -> None:
    manifest = audit_historical_receipts(
        receipt_store=JsonCommitReceiptStore(tmp_path / "receipts.json"),
        ledger=DurableJsonEvidenceLedger(tmp_path / "ledger.json"),
        checkpoint_store=_CheckpointStore(None),
    )

    with pytest.raises(ValueError, match="audit_id"):
        HistoricalReceiptAuditManifest(
            **{
                **manifest.canonical_dict(),
                "audit_id": "forged",
            }
        )
