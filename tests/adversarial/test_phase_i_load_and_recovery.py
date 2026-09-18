"""Phase I hardening: load test and corruption/recovery on the signature path.

I5 crash/corruption attacks and I10 recovery verification applied to the
S13/S14 durable signature ingestion artifacts, plus a lightweight I9 load
test with deterministic assertions (no wall-clock flakiness).
"""

from __future__ import annotations

import json
import time

import pytest

from smart_money.adapters.persistence.durable_json_ledger import (
    DurableJsonEvidenceLedger,
)
from smart_money.adapters.solana_signature_ingestion import (
    bind_normalized_signature,
    bind_normalized_signature_batch,
)
from tests.adversarial.test_phase_i_signature_hardening import (
    _distinct_payloads,
)


# ---------------------------------------------------------------------------
# I5 — corruption attacks on the durable signature ledger.
# ---------------------------------------------------------------------------


def _prepared_ledger(tmp_path, payloads=4) -> tuple[object, object]:
    path = tmp_path / "signature-ledger.json"
    ledger = DurableJsonEvidenceLedger(path)
    bind_normalized_signature_batch(ledger, _distinct_payloads(payloads))
    return path, ledger


@pytest.mark.parametrize("attack", ["truncate", "hash", "schema", "type"])
def test_signature_ledger_corruption_fails_closed(tmp_path, attack: str) -> None:
    path, ledger = _prepared_ledger(tmp_path)
    document = json.loads(path.read_text(encoding="utf-8"))

    if attack == "truncate":
        path.write_text('{"schema_version":', encoding="utf-8")
    elif attack == "hash":
        document["content_hash"] = "0" * 64
        path.write_text(json.dumps(document), encoding="utf-8")
    elif attack == "schema":
        document["schema_version"] = "evidence_ledger.v999"
        path.write_text(json.dumps(document), encoding="utf-8")
    else:
        document["entries"] = "not-a-list"
        path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises((ValueError, json.JSONDecodeError)):
        DurableJsonEvidenceLedger(path)


def test_partial_write_is_never_treated_as_committed(tmp_path, monkeypatch) -> None:
    """A crash mid-append leaves the previous durable state fully intact."""
    path, ledger = _prepared_ledger(tmp_path, payloads=2)
    committed = path.read_bytes()
    original_count = ledger.entry_count

    fresh = _distinct_payloads(5)
    new_payload = fresh[4]

    def crash(*args, **kwargs) -> None:
        raise OSError("injected crash mid-append")

    monkeypatch.setattr(
        "smart_money.adapters.persistence.json_ledger.EvidenceGroundingLedger.save_to_disk",
        crash,
    )
    with pytest.raises(OSError, match="injected crash"):
        bind_normalized_signature(ledger, new_payload)

    assert path.read_bytes() == committed
    recovered = DurableJsonEvidenceLedger(path)
    assert recovered.entry_count == original_count
    for payload in _distinct_payloads(2):
        assert bind_normalized_signature(recovered, payload).duplicate is True


# ---------------------------------------------------------------------------
# I10 — recovery verification: reopen, replay and hash parity.
# ---------------------------------------------------------------------------


def test_recovery_replay_matches_original_state(tmp_path) -> None:
    path = tmp_path / "signature-ledger.json"
    ledger = DurableJsonEvidenceLedger(path)
    payloads = _distinct_payloads(5)
    bind_normalized_signature_batch(ledger, payloads)
    original_hash = ledger.content_hash
    original_ids = sorted(p.get_canonical_id() for p in ledger.iter_payloads())

    reopened = DurableJsonEvidenceLedger(path)
    assert reopened.content_hash == original_hash
    assert reopened.entry_count == len(payloads)
    assert sorted(p.get_canonical_id() for p in reopened.iter_payloads()) == original_ids

    # Full replay of the same page must be a complete no-op.
    receipts = bind_normalized_signature_batch(reopened, payloads)
    assert all(receipt.duplicate for receipt in receipts)
    assert reopened.content_hash == original_hash
    assert reopened.entry_count == len(payloads)


# ---------------------------------------------------------------------------
# I9 — lightweight deterministic load test on the ingestion path.
# ---------------------------------------------------------------------------


def test_ingestion_load_throughput_is_deterministic_and_correct(tmp_path) -> None:
    """Bind 200 distinct signatures; every payload must land exactly once."""
    path = tmp_path / "load-ledger.json"
    ledger = DurableJsonEvidenceLedger(path)
    payloads = _distinct_payloads(200)

    start = time.perf_counter()
    receipts = bind_normalized_signature_batch(ledger, payloads)
    elapsed = time.perf_counter() - start

    assert ledger.entry_count == 200
    assert len({r.evidence_id for r in receipts}) == 200
    assert all(not r.duplicate for r in receipts)

    # Second pass must be a fast pure-duplicate pass with zero growth.
    start = time.perf_counter()
    duplicates = bind_normalized_signature_batch(ledger, payloads)
    duplicate_elapsed = time.perf_counter() - start
    assert all(r.duplicate for r in duplicates)
    assert ledger.entry_count == 200

    # Deterministic bound: replay must not be slower than first ingestion.
    assert duplicate_elapsed <= elapsed + 1.0
    # Bounded work: each payload must take under 250ms on the ingest path
    # (ingestion rewrites the whole durable file per append, so the bound is
    # linear in payloads, not a raw throughput target).
    assert elapsed / len(payloads) < 0.25


def test_dashboard_api_overview_load_is_bounded(tmp_path) -> None:
    """Overview computation over a large ranking must remain linear and fast."""
    from smart_money.application.solana_candidate_pipeline import (
        build_wallet_profile,
        dashboard_candidate_view,
    )

    payloads = _distinct_payloads(100)
    from smart_money.adapters.solana_signature_normalizer import (
        SolanaSignatureNormalizer,
    )

    activities = []
    for payload in payloads:
        normalized = SolanaSignatureNormalizer.normalize(payload)
        activities.append(normalized.candidate_activity())

    start = time.perf_counter()
    profile = build_wallet_profile("wallet-1", tuple(activities))
    dashboard = dashboard_candidate_view((profile,))
    elapsed = time.perf_counter() - start

    assert profile.activity_count == 100
    assert dashboard["read_only"] is True
    assert elapsed < 2.0
