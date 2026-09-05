from __future__ import annotations

import itertools
import json

import pytest

from smart_money.adapters.persistence.json_ledger import EvidenceGroundingLedger
from smart_money.application.solana_decoder import (
    build_transaction_envelope,
    decode_swap_instruction,
    parse_message_instructions,
)
from smart_money.ingestion.contracts import EvidencePayload


def _payload(index: int) -> EvidencePayload:
    return EvidencePayload("corpus", "corpus-event", index, {"index": index})


def test_ledger_corruption_corpus_rejects_schema_variants(tmp_path) -> None:
    path = tmp_path / "ledger.json"
    valid = EvidenceGroundingLedger()
    valid.record(_payload(1))
    valid.save_to_disk(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    cases = []
    for variant in (
        {"schema_version": "evidence_ledger.v9", "entries": []},
        {"schema_version": "evidence_ledger.v2", "entries": []},
        {"schema_version": "evidence_ledger.v1", "content_hash": "x", "entries": []},
        {"schema_version": "evidence_ledger.v2", "content_hash": document["content_hash"], "entries": "bad"},
    ):
        cases.append(variant)
    for index, corrupted in enumerate(cases):
        candidate = tmp_path / f"corrupt-{index}.json"
        candidate.write_text(json.dumps(corrupted), encoding="utf-8")
        with pytest.raises(ValueError):
            EvidenceGroundingLedger().load_from_disk(candidate)


def test_replay_permutations_have_same_membership_and_sorted_projection(tmp_path) -> None:
    payloads = [_payload(index) for index in range(4)]
    memberships = []
    for order in itertools.permutations(range(4)):
        ledger = EvidenceGroundingLedger()
        for index in order:
            ledger.record(payloads[index])
        memberships.append(tuple(sorted(entry.canonical_id for entry in ledger.get_all_entries())))
    assert len(set(memberships)) == 1


def test_duplicate_idempotency_storm_does_not_grow_ledger() -> None:
    ledger = EvidenceGroundingLedger()
    payloads = [_payload(index) for index in range(20)]
    for _ in range(100):
        for item in payloads:
            ledger.record(item)
    assert ledger.entry_count == len(payloads)
    assert len(tuple(ledger.iter_payloads())) == len(payloads)


@pytest.mark.parametrize(
    "signature,slot,message",
    [
        ("", 1, {"instructions": []}),
        ("fake", -1, {"instructions": []}),
        ("fake", 1, {}),
        ("fake", 1, {"instructions": ["not-a-mapping"]}),
        ("fake", 1, {"instructions": [{"type": "SWAP"}]}),
    ],
)
def test_malformed_solana_transaction_corpus_fails_closed(signature, slot, message) -> None:
    if signature and slot >= 0 and message:
        envelope = build_transaction_envelope(signature, slot, message)
        if message.get("instructions") == [{"type": "SWAP"}]:
            with pytest.raises((KeyError, ValueError, TypeError)):
                decode_swap_instruction(message["instructions"][0])
        else:
            with pytest.raises(ValueError):
                parse_message_instructions(envelope)
    else:
        with pytest.raises((ValueError, TypeError, AttributeError)):
            build_transaction_envelope(signature, slot, message)
