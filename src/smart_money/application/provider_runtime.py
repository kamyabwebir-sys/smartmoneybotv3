from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.provider_adapters import ProviderAdapter, normalize_provider_payload
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

def load_solana_rpc_fixture(path: str | Path) -> tuple[dict[str, Any], ...]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise ValueError("Solana RPC fixture must be a list of objects")
    return tuple(raw)

@dataclass(frozen=True, slots=True)
class ProviderPayloadLedgerReceipt:
    evidence_id: str
    already_present: bool

def ingest_provider_payload(adapter: ProviderAdapter, raw: dict[str, Any], ledger: EvidenceLedger) -> ProviderPayloadLedgerReceipt:
    payload = normalize_provider_payload(adapter, raw)
    evidence_id = payload.get_canonical_id()
    present = ledger.contains(evidence_id)
    if ledger.append(payload) != evidence_id:
        raise ValueError("ledger identity mismatch")
    return ProviderPayloadLedgerReceipt(evidence_id, present)

@dataclass(frozen=True, slots=True)
class ProviderConsensus:
    subject_id: str
    value: str
    provider_ids: tuple[str, ...]
    conflicted: bool
    consensus_id: str

def resolve_provider_consensus(subject_id: str, observations: tuple[tuple[str, str], ...]) -> ProviderConsensus:
    if not subject_id.strip() or not observations:
        raise ValueError("subject and observations are required")
    values = tuple(value for _, value in observations)
    value = sorted(set(values))[0]
    conflicted = len(set(values)) > 1
    identity = {"conflicted": conflicted, "provider_ids": tuple(sorted(pid for pid, _ in observations)),
                "schema_version": "provider_consensus.v1", "subject_id": subject_id.strip(), "value": value}
    return ProviderConsensus(subject_id, value, identity["provider_ids"], conflicted,
                             deterministic_id("provider_consensus", identity))

@dataclass(frozen=True, slots=True)
class ProviderReplayVerification:
    evidence_id: str
    matches: bool
    verification_id: str

def verify_provider_replay(adapter: ProviderAdapter, raw: dict[str, Any], payload: EvidencePayload) -> ProviderReplayVerification:
    rebuilt = normalize_provider_payload(adapter, raw)
    matches = rebuilt.get_canonical_id() == payload.get_canonical_id()
    identity = {"evidence_id": payload.get_canonical_id(), "matches": matches,
                "schema_version": "provider_replay.v1"}
    return ProviderReplayVerification(payload.get_canonical_id(), matches,
        deterministic_id("provider_replay", identity))

@dataclass(frozen=True, slots=True)
class ProviderHealthEvidence:
    provider_id: str
    observed_at: int
    fresh: bool
    evidence_id: str
    schema_version: str = "provider_health_evidence.v1"

    def __post_init__(self) -> None:
        if not self.provider_id.strip() or self.observed_at < 0:
            raise ValueError("invalid provider health")
        if self.evidence_id != deterministic_id("provider_health_evidence", {
            "fresh": self.fresh, "observed_at": self.observed_at,
            "provider_id": self.provider_id.strip(), "schema_version": self.schema_version}):
            raise ValueError("evidence_id mismatch")

def build_provider_health_evidence(provider_id: str, *, observed_at: int, fresh: bool) -> ProviderHealthEvidence:
    identity = {"fresh": fresh, "observed_at": observed_at, "provider_id": provider_id.strip(),
                "schema_version": "provider_health_evidence.v1"}
    return ProviderHealthEvidence(provider_id, observed_at, fresh,
                                  deterministic_id("provider_health_evidence", identity))

__all__ = ["load_solana_rpc_fixture", "ProviderPayloadLedgerReceipt", "ingest_provider_payload",
           "ProviderConsensus", "resolve_provider_consensus", "ProviderReplayVerification",
           "verify_provider_replay", "ProviderHealthEvidence", "build_provider_health_evidence"]
