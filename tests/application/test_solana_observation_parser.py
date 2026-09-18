import pytest

from smart_money.application.solana_observation_parser import SolanaObservationParser
from smart_money.domain.solana_observation import SolanaChainObservation
from smart_money.ingestion.contracts import EvidencePayload


def _observation():
    return SolanaChainObservation(
        slot=250,
        observed_at=1_700_000_000,
        transaction_signature="5abc",
        program_id="raydium",
        subject="solana:mainnet-beta:wallet",
        facts={"amount": 10},
    )


def test_parser_round_trips_observation_and_payload():
    projected = SolanaObservationParser.from_observation(_observation())
    parsed = SolanaObservationParser.from_payload(projected.payload)
    assert parsed == projected
    assert parsed.observation_id == _observation().observation_id
    assert parsed.payload.metadata["classification"] == "OBSERVATION"


def test_raw_mapping_parser_is_deterministic():
    raw = {
        "slot": 250,
        "observed_at": 1_700_000_000,
        "transaction_signature": "5abc",
        "program_id": "raydium",
        "subject": "solana:mainnet-beta:wallet",
        "facts": {"amount": 10},
        "commitment": "finalized",
    }
    assert SolanaObservationParser.from_mapping(raw) == SolanaObservationParser.from_mapping(
        dict(reversed(tuple(raw.items())))
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("evidence_type", "generic", "evidence_type"),
        ("metadata", {"authority": "NONE"}, "provenance"),
    ],
)
def test_payload_parser_fails_closed(field, value, message):
    original = SolanaObservationParser.from_observation(_observation()).payload
    values = {
        "source_id": original.source_id,
        "evidence_type": original.evidence_type,
        "timestamp": original.timestamp,
        "data": original.data,
        "metadata": original.metadata,
    }
    if field == "metadata":
        value = {"authority": "NONE"}
    values[field] = value
    payload = EvidencePayload(**values)
    with pytest.raises(ValueError, match=message):
        SolanaObservationParser.from_payload(payload)


def test_raw_mapping_rejects_extra_keys():
    raw = {
        "slot": 1,
        "observed_at": 1,
        "transaction_signature": "sig",
        "program_id": "program",
        "subject": "wallet",
        "facts": {},
        "commitment": "finalized",
        "extra": 1,
    }
    with pytest.raises(ValueError, match="keys"):
        SolanaObservationParser.from_mapping(raw)
