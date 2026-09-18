from __future__ import annotations

import json

import pytest

from smart_money.adapters.persistence import json_ledger
from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.ingestion.contracts import EvidencePayload


def payload(sequence: int) -> EvidencePayload:
    return EvidencePayload(
        source_id="q1-adversarial",
        evidence_type="crash-test",
        timestamp=sequence,
        data={"sequence": sequence},
    )


def test_replace_crash_preserves_previous_committed_ledger(tmp_path, monkeypatch) -> None:
    path = tmp_path / "ledger.json"
    ledger = EvidenceGroundingLedger()
    first_id = ledger.record(payload(1))
    ledger.save_to_disk(path)
    committed = path.read_bytes()

    ledger.record(payload(2))

    def crash_before_replace(source, destination) -> None:
        raise OSError("injected crash before replace")

    monkeypatch.setattr(json_ledger, "atomic_replace", crash_before_replace)
    with pytest.raises(OSError, match="injected crash"):
        ledger.save_to_disk(path)

    assert path.read_bytes() == committed
    recovered = EvidenceGroundingLedger()
    recovered.load_from_disk(path)
    assert recovered.entry_count == 1
    assert recovered.contains(first_id)


@pytest.mark.parametrize("attack", ["truncate", "hash", "identity", "duplicate"])
def test_corruption_attacks_fail_closed(tmp_path, attack: str) -> None:
    path = tmp_path / "ledger.json"
    ledger = EvidenceGroundingLedger()
    ledger.record(payload(7))
    ledger.save_to_disk(path)
    document = json.loads(path.read_text(encoding="utf-8"))

    if attack == "truncate":
        path.write_text('{"schema_version":', encoding="utf-8")
    elif attack == "hash":
        document["content_hash"] = "0" * 64
        path.write_text(json.dumps(document), encoding="utf-8")
    elif attack == "identity":
        document["entries"][0]["canonical_id"] = "evidence_" + "0" * 32
        document["content_hash"] = ledger._compute_content_hash(document["entries"])
        path.write_text(json.dumps(document), encoding="utf-8")
    else:
        document["entries"].append(document["entries"][0])
        document["content_hash"] = ledger._compute_content_hash(document["entries"])
        path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError):
        EvidenceGroundingLedger().load_from_disk(path)
