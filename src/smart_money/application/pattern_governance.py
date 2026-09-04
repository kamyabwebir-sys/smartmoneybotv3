from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from smart_money.application.pattern_discovery import PatternObservation, PatternEvidenceProjection
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class PatternLedgerReceipt:
    observation_id: str
    evidence_id: str
    already_present: bool

def ingest_pattern_evidence(pattern: PatternObservation, ledger: EvidenceLedger) -> PatternLedgerReceipt:
    if not isinstance(pattern, PatternObservation) or not isinstance(ledger, EvidenceLedger):
        raise TypeError("invalid pattern or ledger")
    payload = PatternEvidenceProjection.from_binding(
        _single_pattern_binding(pattern)
    ).payload
    evidence_id = payload.get_canonical_id()
    present = ledger.contains(evidence_id)
    if ledger.append(payload) != evidence_id:
        raise ValueError("ledger identity mismatch")
    return PatternLedgerReceipt(pattern.observation_id, evidence_id, present)

def _single_pattern_binding(pattern: PatternObservation):
    from smart_money.application.pattern_discovery import CrossSubjectPatternBinding
    identity = {"schema_version":"cross_subject_pattern_binding.v1","token_pattern_id":pattern.observation_id,"wallet_pattern_id":pattern.observation_id}
    return CrossSubjectPatternBinding(pattern.observation_id, pattern.observation_id, deterministic_id("cross_subject_pattern_binding", identity))

class PatternPersistenceStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, PatternObservation] = {}
    def save(self, pattern: PatternObservation) -> str:
        if not isinstance(pattern, PatternObservation):
            raise TypeError("pattern must be PatternObservation")
        self._items[pattern.observation_id]=pattern
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps({"schema_version":"pattern_store.v1","items":[x.canonical_dict() for x in self._items.values()]},sort_keys=True,separators=(",",":")),encoding="utf-8")
        return pattern.observation_id
    def get(self, observation_id: str) -> PatternObservation | None: return self._items.get(observation_id)

@dataclass(frozen=True, slots=True)
class PatternStoreReplayVerification:
    observation_id: str
    matches: bool
    verification_id: str
    schema_version: str = "pattern_store_replay.v1"

def verify_pattern_store(pattern: PatternObservation, store: PatternPersistenceStore) -> PatternStoreReplayVerification:
    matches=store.get(pattern.observation_id)==pattern
    identity={"observation_id":pattern.observation_id,"matches":matches,"schema_version":"pattern_store_replay.v1"}
    return PatternStoreReplayVerification(pattern.observation_id,matches,deterministic_id("pattern_store_replay",identity))

@dataclass(frozen=True, slots=True)
class PatternRegistryProposal:
    observation_id: str
    rationale: str
    proposal_id: str
    schema_version: str = "pattern_registry_proposal.v1"
    def __post_init__(self) -> None:
        if not self.rationale.strip():
            raise ValueError("rationale must be non-empty")
        if self.proposal_id != deterministic_id("pattern_registry_proposal", {"observation_id":self.observation_id,"rationale":self.rationale.strip(),"schema_version":self.schema_version}):
            raise ValueError("proposal_id mismatch")

def propose_pattern(pattern: PatternObservation, rationale: str) -> PatternRegistryProposal:
    identity={"observation_id":pattern.observation_id,"rationale":rationale.strip(),"schema_version":"pattern_registry_proposal.v1"}
    return PatternRegistryProposal(pattern.observation_id,rationale,deterministic_id("pattern_registry_proposal",identity))

@dataclass(frozen=True, slots=True)
class PatternCandidateRanked:
    observation_id: str
    rank: int
    score: int

def rank_pattern_candidates(patterns: tuple[PatternObservation, ...]) -> tuple[PatternCandidateRanked, ...]:
    ordered=sorted(patterns,key=lambda x:(x.kind.value,x.subject_id,x.observation_id))
    return tuple(PatternCandidateRanked(x.observation_id,i,len(ordered)-i+1) for i,x in enumerate(ordered,1))

__all__=["PatternLedgerReceipt","ingest_pattern_evidence","PatternPersistenceStore","PatternStoreReplayVerification","verify_pattern_store","PatternRegistryProposal","propose_pattern","PatternCandidateRanked","rank_pattern_candidates"]
