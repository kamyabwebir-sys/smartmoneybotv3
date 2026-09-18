from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.domain.wallet_intelligence import WalletIntelligenceObservation
from smart_money.application.token_safety_candidate_binding import TokenSafetyCandidateBinding
from smart_money.core.ids import deterministic_id

@dataclass(frozen=True, slots=True)
class WalletTokenCrossSubjectContract:
    candidate_id: str
    wallet: str
    token: str
    wallet_observation_id: str
    safety_binding_id: str
    cross_id: str
    schema_version: str = "wallet_token_cross_subject.v1"
    def __post_init__(self) -> None:
        for name in ("candidate_id","wallet","token","wallet_observation_id","safety_binding_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.cross_id != deterministic_id("wallet_token_cross_subject", self._identity()):
            raise ValueError("cross_id mismatch")
    def _identity(self)->dict[str,Any]:
        return {"candidate_id":self.candidate_id,"schema_version":self.schema_version,"safety_binding_id":self.safety_binding_id,"token":self.token.strip(),"wallet":self.wallet.strip(),"wallet_observation_id":self.wallet_observation_id}
    def canonical_dict(self)->dict[str,Any]: return {**self._identity(),"cross_id":self.cross_id}

def bind_cross_subject(candidate: SolanaWalletTokenCandidate, wallet: WalletIntelligenceObservation, safety: TokenSafetyCandidateBinding)->WalletTokenCrossSubjectContract:
    if candidate.wallet != wallet.wallet or candidate.wallet != safety.wallet or candidate.mint != safety.token:
        raise ValueError("cross-subject identity mismatch")
    identity={"candidate_id":candidate.candidate_id,"schema_version":"wallet_token_cross_subject.v1","safety_binding_id":safety.binding_id,"token":candidate.mint,"wallet":candidate.wallet,"wallet_observation_id":wallet.observation_id}
    return WalletTokenCrossSubjectContract(candidate.candidate_id,candidate.wallet,candidate.mint,wallet.observation_id,safety.binding_id,deterministic_id("wallet_token_cross_subject",identity))

@dataclass(frozen=True, slots=True)
class CrossIntelligenceEvidenceProjection:
    payload: Any
    cross_id: str
    @classmethod
    def from_contract(cls, contract: WalletTokenCrossSubjectContract)->"CrossIntelligenceEvidenceProjection":
        from smart_money.ingestion.contracts import EvidencePayload
        return cls(EvidencePayload(source_id="cross-intelligence",evidence_type="wallet_token_cross_intelligence",timestamp=0,data={"cross_subject":contract.canonical_dict()},metadata={"authority":"NONE","classification":"EVIDENCE","verification_status":"UNKNOWN","provenance":{"cross_id":contract.cross_id}}),contract.cross_id)

@dataclass(frozen=True, slots=True)
class CrossIntelligenceReplayVerification:
    cross_id: str
    matches: bool
    verification_id: str
    schema_version: str = "cross_intelligence_replay.v1"

def verify_cross_intelligence_replay(contract: WalletTokenCrossSubjectContract, projection: CrossIntelligenceEvidenceProjection)->CrossIntelligenceReplayVerification:
    rebuilt=CrossIntelligenceEvidenceProjection.from_contract(contract)
    matches=rebuilt.payload.get_canonical_id()==projection.payload.get_canonical_id()
    return CrossIntelligenceReplayVerification(contract.cross_id,matches,deterministic_id("cross_intelligence_replay",{"cross_id":contract.cross_id,"matches":matches,"schema_version":"cross_intelligence_replay.v1"}))

__all__=["WalletTokenCrossSubjectContract","bind_cross_subject","CrossIntelligenceEvidenceProjection","CrossIntelligenceReplayVerification","verify_cross_intelligence_replay"]
