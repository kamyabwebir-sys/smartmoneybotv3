from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any
from smart_money.core.ids import deterministic_id
from smart_money.ingestion.contracts import EvidencePayload

class PatternKind(str, Enum):
    WALLET_BEHAVIOR = "WALLET_BEHAVIOR"
    TOKEN_DISCOVERY = "TOKEN_DISCOVERY"

@dataclass(frozen=True, slots=True)
class PatternObservation:
    subject_id: str
    kind: PatternKind
    features: tuple[str, ...]
    source_id: str
    observation_id: str
    schema_version: str = "pattern_observation.v1"
    def __post_init__(self) -> None:
        if not isinstance(self.subject_id, str) or not self.subject_id.strip():
            raise ValueError("subject_id must be non-empty")
        if not isinstance(self.kind, PatternKind):
            raise TypeError("kind must be PatternKind")
        if not isinstance(self.features, tuple) or not self.features or not all(isinstance(x, str) and x.strip() for x in self.features):
            raise ValueError("features must be non-empty text tuple")
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise ValueError("source_id must be non-empty")
        if self.observation_id != deterministic_id("pattern_observation", self.identity_payload()):
            raise ValueError("observation_id mismatch")
    def identity_payload(self) -> dict[str, Any]:
        return {"features": self.features, "kind": self.kind.value, "schema_version": self.schema_version,
                "source_id": self.source_id.strip(), "subject_id": self.subject_id.strip()}
    def canonical_dict(self) -> dict[str, Any]:
        return {"observation_id": self.observation_id, **self.identity_payload()}

def extract_wallet_behavior_pattern(wallet_id: str, *, features: tuple[str, ...], source_id: str) -> PatternObservation:
    identity={"features":features,"kind":"WALLET_BEHAVIOR","schema_version":"pattern_observation.v1","source_id":source_id.strip(),"subject_id":wallet_id.strip()}
    return PatternObservation(wallet_id, PatternKind.WALLET_BEHAVIOR, features, source_id, deterministic_id("pattern_observation", identity))

def extract_token_discovery_pattern(token_id: str, *, features: tuple[str, ...], source_id: str) -> PatternObservation:
    identity={"features":features,"kind":"TOKEN_DISCOVERY","schema_version":"pattern_observation.v1","source_id":source_id.strip(),"subject_id":token_id.strip()}
    return PatternObservation(token_id, PatternKind.TOKEN_DISCOVERY, features, source_id, deterministic_id("pattern_observation", identity))

@dataclass(frozen=True, slots=True)
class CrossSubjectPatternBinding:
    wallet_pattern_id: str
    token_pattern_id: str
    binding_id: str
    schema_version: str = "cross_subject_pattern_binding.v1"
    def __post_init__(self) -> None:
        if not self.wallet_pattern_id.strip() or not self.token_pattern_id.strip():
            raise ValueError("pattern IDs must be non-empty")
        if self.binding_id != deterministic_id("cross_subject_pattern_binding", self.identity_payload()):
            raise ValueError("binding_id mismatch")
    def identity_payload(self) -> dict[str, Any]:
        return {"schema_version":self.schema_version,"token_pattern_id":self.token_pattern_id.strip(),"wallet_pattern_id":self.wallet_pattern_id.strip()}
    def canonical_dict(self) -> dict[str, Any]:
        return {"binding_id":self.binding_id,**self.identity_payload()}

def bind_patterns(wallet: PatternObservation, token: PatternObservation) -> CrossSubjectPatternBinding:
    if wallet.kind is not PatternKind.WALLET_BEHAVIOR or token.kind is not PatternKind.TOKEN_DISCOVERY:
        raise ValueError("pattern kinds do not match")
    identity={"schema_version":"cross_subject_pattern_binding.v1","token_pattern_id":token.observation_id,"wallet_pattern_id":wallet.observation_id}
    return CrossSubjectPatternBinding(wallet.observation_id, token.observation_id, deterministic_id("cross_subject_pattern_binding", identity))

@dataclass(frozen=True, slots=True)
class PatternEvidenceProjection:
    payload: EvidencePayload
    binding_id: str
    @classmethod
    def from_binding(cls, binding: CrossSubjectPatternBinding) -> "PatternEvidenceProjection":
        payload=EvidencePayload(source_id="pattern-discovery", evidence_type="cross_subject_pattern",
            data={"binding":binding.canonical_dict()}, metadata={"authority":"NONE","classification":"EVIDENCE","verification_status":"UNKNOWN","provenance":{"binding_id":binding.binding_id}})
        return cls(payload,binding.binding_id)

def verify_pattern_replay(binding: CrossSubjectPatternBinding, projection: PatternEvidenceProjection) -> bool:
    return PatternEvidenceProjection.from_binding(binding).payload.get_canonical_id() == projection.payload.get_canonical_id()

def query_patterns(patterns: tuple[PatternObservation, ...], *, kind: PatternKind | None = None, subject_id: str | None = None) -> tuple[PatternObservation, ...]:
    if not isinstance(patterns, tuple):
        raise TypeError("patterns must be tuple")
    return tuple(x for x in patterns if (kind is None or x.kind is kind) and (subject_id is None or x.subject_id == subject_id.strip()))

@dataclass(frozen=True, slots=True)
class PatternQueryAudit:
    result_count: int
    query_id: str
    audit_id: str
    schema_version: str = "pattern_query_audit.v1"
    def __post_init__(self) -> None:
        expected=deterministic_id("pattern_query_audit",{"query_id":self.query_id,"result_count":self.result_count,"schema_version":self.schema_version})
        if self.audit_id != expected:
            raise ValueError("audit_id mismatch")

def audit_pattern_query(patterns: tuple[PatternObservation, ...]) -> PatternQueryAudit:
    query_id=deterministic_id("pattern_query",{"observation_ids":tuple(x.observation_id for x in patterns),"schema_version":"pattern_query.v1"})
    identity={"query_id":query_id,"result_count":len(patterns),"schema_version":"pattern_query_audit.v1"}
    return PatternQueryAudit(len(patterns),query_id,deterministic_id("pattern_query_audit",identity))

__all__=["PatternKind","PatternObservation","extract_wallet_behavior_pattern","extract_token_discovery_pattern","CrossSubjectPatternBinding","bind_patterns","PatternEvidenceProjection","verify_pattern_replay","query_patterns","PatternQueryAudit","audit_pattern_query"]
