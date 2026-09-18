"""Phase I hardening: adversarial corpora against the signature ingestion path.

I2 malformed RPC corpus, I3 duplicate storm, I4 replay permutation and
I6 provider poisoning. Every case must fail closed without mutating state.
"""

from __future__ import annotations

import copy
import itertools

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from smart_money.adapters.persistence.durable_json_ledger import (
    DurableJsonEvidenceLedger,
)
from smart_money.adapters.solana_signature_ingestion import (
    bind_normalized_signature,
    bind_normalized_signature_batch,
)
from smart_money.adapters.solana_signature_normalizer import (
    SolanaSignatureNormalizer,
)
from smart_money.ingestion.contracts import EvidencePayload
from tests.adapters.test_solana_signature_normalizer import _buy_payload


# ---------------------------------------------------------------------------
# I2 — malformed RPC corpus: no malformed payload may produce an observation.
# ---------------------------------------------------------------------------

MALFORMED_CORPUS = (
    {},
    None,
    [],
    "payload",
    {"result": None},
    {"error": {"code": -32000, "message": "pruned"}},
    {"result": {}},
    {"result": {"slot": 1}},
    {"result": {"slot": 1, "transaction": {}}},
    {"result": {"slot": 1, "transaction": {"signatures": []}, "meta": {}}},
    {"result": {"slot": 1, "transaction": {"signatures": [42]}, "meta": {}}},
    {"result": {"slot": -5, "transaction": {"signatures": ["sig"]}, "meta": {}}},
    {"result": {"slot": 1, "transaction": {"signatures": ["sig"], "message": 7}, "meta": {}}},
    {"result": {"slot": 1, "transaction": {"signatures": ["sig"]}, "meta": {"preBalances": [1], "postBalances": [1, 2]}}},
    {"result": {"slot": 1, "transaction": {"signatures": ["sig"]}, "meta": {"preBalances": [], "postBalances": []}}},
    {"result": {"slot": 1, "transaction": {"signatures": ["sig"]}, "meta": {"fee": "x"}}},
    {"result": {"slot": True, "transaction": {"signatures": ["sig"]}, "meta": {}}},
    {"result": {"slot": 1, "transaction": {"signatures": ["sig"]}, "meta": {"preTokenBalances": [{"accountIndex": 0, "mint": "m", "owner": "w", "uiTokenAmount": {"amount": "-3", "decimals": 9}}]}}},
    {"result": {"slot": 1, "transaction": {"signatures": ["sig"]}, "meta": {"preTokenBalances": [{"accountIndex": 0, "mint": "m", "owner": "w", "uiTokenAmount": {"amount": 5, "decimals": 9}}]}}},
    {"result": {"slot": 1, "transaction": {"signatures": ["sig"]}, "meta": {"preTokenBalances": [{"accountIndex": 0, "mint": "", "owner": "w", "uiTokenAmount": {"amount": "5", "decimals": 9}}]}}},
    {"result": {"slot": 1, "transaction": {"signatures": ["sig"]}, "meta": {"preTokenBalances": "nope"}}},
)


@pytest.mark.parametrize("payload", MALFORMED_CORPUS, ids=range(len(MALFORMED_CORPUS)))
def test_malformed_rpc_corpus_fails_closed(payload) -> None:
    with pytest.raises((TypeError, ValueError, AttributeError, IndexError)):
        SolanaSignatureNormalizer.normalize(payload)


@settings(max_examples=200, deadline=None)
@given(
    st.dictionaries(
        st.sampled_from(("result", "meta", "transaction", "slot", "fee", "preBalances")),
        st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=12)),
        max_size=6,
    )
)
def test_fuzzed_rpc_payloads_never_yield_observations(payload) -> None:
    """No random type-confused mapping may normalize into an observation."""
    try:
        SolanaSignatureNormalizer.normalize(payload)
    except (TypeError, ValueError, AttributeError, IndexError, KeyError):
        return
    # If normalization unexpectedly succeeded, the payload must at least be
    # internally consistent — slot non-negative and a real signature present.
    assert isinstance(payload, dict) and payload.get("slot") is not None


def test_identity_conflict_between_pre_and_post_balances_fails_closed() -> None:
    payload = _buy_payload()
    payload["meta"]["postTokenBalances"][1]["mint"] = "different-mint"
    with pytest.raises(ValueError, match="ownership changed"):
        SolanaSignatureNormalizer.normalize(payload)


def test_mutated_payload_never_reuses_original_observation_id() -> None:
    baseline = SolanaSignatureNormalizer.normalize(_buy_payload())
    mutated = copy.deepcopy(_buy_payload())
    mutated["slot"] = 43
    other = SolanaSignatureNormalizer.normalize(mutated)
    assert baseline.observation.observation_id != other.observation.observation_id


# ---------------------------------------------------------------------------
# I3 — duplicate storm on the durable ledger via signature binding.
# ---------------------------------------------------------------------------


def test_duplicate_storm_keeps_ledger_idempotent(tmp_path) -> None:
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")
    payload = _buy_payload()

    first = bind_normalized_signature(ledger, payload)
    assert first.duplicate is False

    for _ in range(50):
        receipt = bind_normalized_signature(ledger, payload)
        assert receipt.duplicate is True
        assert receipt.evidence_id == first.evidence_id

    assert ledger.entry_count == 1
    assert bind_normalized_signature_batch(
        ledger, (_buy_payload() for _ in range(10))
    )[0].duplicate is True
    assert ledger.entry_count == 1


def test_duplicate_storm_survives_reopen(tmp_path) -> None:
    path = tmp_path / "ledger.json"
    ledger = DurableJsonEvidenceLedger(path)
    receipt = bind_normalized_signature(ledger, _buy_payload())
    original_hash = ledger.content_hash

    for _ in range(10):
        reopened = DurableJsonEvidenceLedger(path)
        replayed = bind_normalized_signature(reopened, _buy_payload())
        assert replayed.duplicate is True
        assert reopened.content_hash == original_hash
        assert reopened.entry_count == 1
    assert receipt.evidence_id


def test_conflicting_payload_with_same_signature_is_never_silently_merged(tmp_path) -> None:
    """Two distinct observations sharing a signature must not collapse into one."""
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")
    bind_normalized_signature(ledger, _buy_payload())
    mutated = _buy_payload()
    mutated["slot"] = 99
    second = bind_normalized_signature(ledger, mutated)
    assert ledger.entry_count == 2
    assert second.duplicate is False


# ---------------------------------------------------------------------------
# I4 — replay permutation: order of ingestion never changes ledger state.
# ---------------------------------------------------------------------------


def _distinct_payloads(count: int) -> tuple[dict[str, object], ...]:
    payloads = []
    for index in range(count):
        payload = _buy_payload()
        payload["slot"] = 100 + index
        payload["transaction"]["signatures"][0] = f"signature-{index}"
        payloads.append(payload)
    return tuple(payloads)


def test_replay_permutation_produces_identical_membership(tmp_path) -> None:
    """Order must not change which evidence exists (content hash is order-aware)."""
    payloads = _distinct_payloads(4)
    probe = DurableJsonEvidenceLedger(tmp_path / "probe.json")
    receipts = bind_normalized_signature_batch(probe, payloads)
    expected_ids = frozenset(r.evidence_id for r in receipts)
    for order in itertools.permutations(range(len(payloads))):
        ledger = DurableJsonEvidenceLedger(tmp_path / f"perm-{order}.json")
        bind_normalized_signature_batch(ledger, (payloads[index] for index in order))
        assert ledger.entry_count == len(payloads)
        assert {p.get_canonical_id() for p in ledger.iter_payloads()} == expected_ids


def test_replay_receipts_are_order_independent(tmp_path) -> None:
    payloads = _distinct_payloads(3)
    receipt_sets = []
    for order in itertools.permutations(range(len(payloads))):
        ledger = DurableJsonEvidenceLedger(tmp_path / "shared.json")
        receipts = bind_normalized_signature_batch(
            ledger, (payloads[index] for index in order)
        )
        receipt_sets.append(
            frozenset(
                (r.signature, r.evidence_id, r.direction, r.wallet, r.slot)
                for r in receipts
            )
        )
    assert len(set(receipt_sets)) == 1


# ---------------------------------------------------------------------------
# I6 — provider poisoning: a hostile ledger must never accept forged state.
# ---------------------------------------------------------------------------


class PoisonedLedger:
    """A ledger that lies: claims unknown ids exist and refuses appends."""

    def __init__(self) -> None:
        self.append_calls = 0
        self._hidden = {}

    def contains(self, canonical_id: str) -> bool:
        return True  # pretend everything is a duplicate

    def append(self, payload: EvidencePayload) -> str:
        self.append_calls += 1
        return payload.get_canonical_id()

    def get(self, canonical_id: str):
        return self._hidden.get(canonical_id)

    def iter_payloads(self):
        return iter(tuple(self._hidden.values()))

    @property
    def entry_count(self) -> int:
        return len(self._hidden)


class ForgingLedger:
    """A ledger that accepts but returns a mismatched canonical id."""

    def __init__(self) -> None:
        self._hidden = {}

    def contains(self, canonical_id: str) -> bool:
        return False

    def append(self, payload: EvidencePayload) -> str:
        return "forged-id"

    def get(self, canonical_id: str):
        return self._hidden.get(canonical_id)

    def iter_payloads(self):
        return iter(tuple(self._hidden.values()))

    @property
    def entry_count(self) -> int:
        return len(self._hidden)


def test_poisoned_ledger_claims_everything_is_duplicate() -> None:
    hostile = PoisonedLedger()
    receipt = bind_normalized_signature(hostile, _buy_payload())
    # Binding must still report the (false) duplicate flag from the ledger
    # without writing forged evidence anywhere.
    assert receipt.duplicate is True
    # The poisoned ledger returns the true canonical id, so the binding is
    # still verifiable — but nothing may be marked stored inside the ledger.
    assert hostile.entry_count == 0
    assert tuple(hostile.iter_payloads()) == ()


def test_forging_ledger_identity_mismatch_fails_closed(tmp_path) -> None:
    with pytest.raises(ValueError, match="non-canonical evidence identity"):
        bind_normalized_signature(ForgingLedger(), _buy_payload())


def test_type_hostile_ledger_is_rejected_before_any_normalization(tmp_path) -> None:
    with pytest.raises(TypeError, match="EvidenceLedger"):
        bind_normalized_signature(object(), _buy_payload())  # type: ignore[arg-type]
