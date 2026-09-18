import json
from decimal import Decimal

import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.macro_evidence_projection import (
    ExternalMacroEvidenceProjection,
)
from smart_money.application.macro_ledger_ingestion import (
    ingest_macro_evidence,
)
from smart_money.application.macro_replay import verify_macro_evidence_replay
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)


def _observation() -> MacroEvidenceObservation:
    return MacroEvidenceObservation(
        source_id="worldmonitor",
        metric="risk_sentiment",
        observed_at=1_700_000_000,
        value=Decimal("0.25"),
        unit="index",
        status=MacroObservationStatus.PROVISIONAL,
        source_revision="r1",
    )


def test_persisted_macro_evidence_replays_identically(tmp_path) -> None:
    path = tmp_path / "macro-ledger.json"
    original = EvidenceGroundingLedger()
    ingest_macro_evidence(_observation(), original)
    original.save_to_disk(path)
    first_bytes = path.read_bytes()

    restored = EvidenceGroundingLedger()
    restored.load_from_disk(path)
    receipt = verify_macro_evidence_replay(_observation(), restored)

    restored.save_to_disk(path)
    assert path.read_bytes() == first_bytes
    assert receipt.evidence_id == (
        ExternalMacroEvidenceProjection.from_observation(
            _observation()
        ).payload.get_canonical_id()
    )
    assert receipt.ledger_entry_count == 1
    assert receipt.receipt_id == verify_macro_evidence_replay(
        _observation(),
        restored,
    ).receipt_id


def test_corrupted_ledger_content_hash_is_rejected(tmp_path) -> None:
    path = tmp_path / "macro-ledger.json"
    ledger = EvidenceGroundingLedger()
    ingest_macro_evidence(_observation(), ledger)
    ledger.save_to_disk(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["content_hash"] = "0" * 64
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="content hash mismatch"):
        EvidenceGroundingLedger().load_from_disk(path)


def test_replay_rejects_changed_source_observation(tmp_path) -> None:
    path = tmp_path / "macro-ledger.json"
    ledger = EvidenceGroundingLedger()
    ingest_macro_evidence(_observation(), ledger)
    ledger.save_to_disk(path)
    restored = EvidenceGroundingLedger()
    restored.load_from_disk(path)

    changed = MacroEvidenceObservation(
        source_id="worldmonitor",
        metric="risk_sentiment",
        observed_at=1_700_000_000,
        value=Decimal("0.26"),
        unit="index",
        status=MacroObservationStatus.PROVISIONAL,
        source_revision="r1",
    )
    with pytest.raises(ValueError, match="missing from Ledger"):
        verify_macro_evidence_replay(changed, restored)
