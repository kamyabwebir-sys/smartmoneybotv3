from smart_money.application.candidate_safety_funding_gate import (
    CandidateEvidenceGateStatus,
    HolderConcentrationEvidence,
    LiquidityPoolEvidence,
    TokenAuthorityEvidence,
    TokenLifecycleRiskEvidence,
    bind_candidate_safety_funding,
)
from smart_money.core.ids import deterministic_id


def evidence(cls, namespace: str, **identity):
    return cls(evidence_id=deterministic_id(namespace, identity), **identity)


def complete_values():
    authority_identity = {"freeze_authority": None, "mint": "M", "mint_authority": None, "observed_slot": 1, "schema_version": "token_authority_evidence.v1", "source_id": "rpc"}
    concentration_identity = {"holder_count": 100, "mint": "M", "observed_slot": 1, "schema_version": "holder_concentration_evidence.v1", "source_id": "provider", "top_holders_bps": 2000}
    liquidity_identity = {"base_reserve_raw": 100, "mint": "M", "observed_slot": 1, "pool": "P", "quote_mint": "USDC", "quote_reserve_raw": 100, "schema_version": "liquidity_pool_evidence.v1", "source_id": "rpc"}
    lifecycle_identity = {"lifecycle_id": "L", "mint": "M", "phase": "TRADING", "risk_codes": (), "schema_version": "token_lifecycle_risk_evidence.v1"}
    return (
        evidence(TokenAuthorityEvidence, "token-authority-evidence", **authority_identity),
        evidence(HolderConcentrationEvidence, "holder-concentration-evidence", **concentration_identity),
        evidence(LiquidityPoolEvidence, "liquidity-pool-evidence", **liquidity_identity),
        evidence(TokenLifecycleRiskEvidence, "token-lifecycle-risk-evidence", **lifecycle_identity),
    )


def test_missing_data_is_incomplete_not_safe() -> None:
    result = bind_candidate_safety_funding(candidate_id="c", wallet="w", mint="M", authority=None, concentration=None, liquidity=None, lifecycle=None)
    assert result.status is CandidateEvidenceGateStatus.INCOMPLETE
    assert "INCOMPLETE_SAFETY_EVIDENCE" in result.reason_codes


def test_complete_safe_evidence_with_funding_is_eligible() -> None:
    authority, concentration, liquidity, lifecycle = complete_values()
    result = bind_candidate_safety_funding(candidate_id="c", wallet="w", mint="M", authority=authority, concentration=concentration, liquidity=liquidity, lifecycle=lifecycle, funding_edge_ids=("edge",), related_wallets=("r",))
    assert result.status is CandidateEvidenceGateStatus.ELIGIBLE
    assert not result.reason_codes


def test_observed_risk_blocks_candidate() -> None:
    authority, concentration, liquidity, lifecycle = complete_values()
    identity = authority.identity_payload() | {"mint_authority": "active"}
    authority = evidence(TokenAuthorityEvidence, "token-authority-evidence", **identity)
    result = bind_candidate_safety_funding(candidate_id="c", wallet="w", mint="M", authority=authority, concentration=concentration, liquidity=liquidity, lifecycle=lifecycle, funding_edge_ids=("edge",))
    assert result.status is CandidateEvidenceGateStatus.BLOCKED
    assert "MINT_AUTHORITY_ACTIVE" in result.reason_codes
