from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

class ProviderAdapter(Protocol):
    provider_id: str
    def normalize(self, raw: Mapping[str, Any]) -> EvidencePayload: ...

@dataclass(frozen=True, slots=True)
class SolanaRPCObservationAdapter:
    provider_id: str = "solana-rpc"
    def normalize(self, raw: Mapping[str, Any]) -> EvidencePayload:
        return _payload(self.provider_id, "solana_rpc_observation", raw)

@dataclass(frozen=True, slots=True)
class TokenMetadataProviderAdapter:
    provider_id: str = "token-metadata"
    def normalize(self, raw: Mapping[str, Any]) -> EvidencePayload:
        return _payload(self.provider_id, "token_metadata_observation", raw)

@dataclass(frozen=True, slots=True)
class LiquidityPoolProviderAdapter:
    provider_id: str = "liquidity-pool"
    def normalize(self, raw: Mapping[str, Any]) -> EvidencePayload:
        return _payload(self.provider_id, "liquidity_pool_observation", raw)

@dataclass(frozen=True, slots=True)
class WalletActivityProviderAdapter:
    provider_id: str = "wallet-activity"
    def normalize(self, raw: Mapping[str, Any]) -> EvidencePayload:
        return _payload(self.provider_id, "wallet_activity_observation", raw)

def normalize_provider_payload(adapter: ProviderAdapter, raw: Mapping[str, Any]) -> EvidencePayload:
    if not isinstance(raw, Mapping):
        raise TypeError("raw must be a mapping")
    payload = adapter.normalize(raw)
    if not isinstance(payload, EvidencePayload):
        raise TypeError("adapter must return EvidencePayload")
    return payload

def _payload(source: str, evidence_type: str, raw: Mapping[str, Any]) -> EvidencePayload:
    if not raw:
        raise ValueError("raw provider payload must be non-empty")
    timestamp = raw.get("timestamp", raw.get("slot", 0))
    if isinstance(timestamp, bool) or not isinstance(timestamp, int) or timestamp < 0:
        raise ValueError("timestamp must be non-negative integer")
    return EvidencePayload(source_id=source, evidence_type=evidence_type, timestamp=timestamp,
                           data={"raw": dict(raw)},
                           metadata={"authority":"EXTERNAL_NON_AUTHORITATIVE",
                                     "classification":"EVIDENCE",
                                     "verification_status":"UNKNOWN",
                                     "provenance":{"provider_id":source}})

@dataclass(frozen=True, slots=True)
class ProviderConflictEvidence:
    subject_id: str
    provider_ids: tuple[str, ...]
    conflict_code: str
    evidence_id: str
    schema_version: str = "provider_conflict_evidence.v1"
    def __post_init__(self) -> None:
        if not self.subject_id.strip() or len(self.provider_ids) < 2 or not self.conflict_code.strip():
            raise ValueError("invalid provider conflict")
        if self.evidence_id != deterministic_id("provider_conflict_evidence", self.identity_payload()):
            raise ValueError("evidence_id mismatch")
    def identity_payload(self) -> dict[str, Any]:
        return {"conflict_code":self.conflict_code.strip(),"provider_ids":self.provider_ids,
                "schema_version":self.schema_version,"subject_id":self.subject_id.strip()}

def build_provider_conflict_evidence(subject_id: str, provider_ids: tuple[str, ...], conflict_code: str) -> ProviderConflictEvidence:
    identity={"conflict_code":conflict_code.strip(),"provider_ids":provider_ids,
              "schema_version":"provider_conflict_evidence.v1","subject_id":subject_id.strip()}
    return ProviderConflictEvidence(subject_id, provider_ids, conflict_code,
                                    deterministic_id("provider_conflict_evidence", identity))

__all__=["ProviderAdapter","SolanaRPCObservationAdapter","TokenMetadataProviderAdapter",
         "LiquidityPoolProviderAdapter","WalletActivityProviderAdapter",
         "normalize_provider_payload","ProviderConflictEvidence","build_provider_conflict_evidence"]
