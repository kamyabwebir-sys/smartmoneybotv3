"""Fail-closed binding of independently sourced token-safety and funding evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from smart_money.core.ids import deterministic_id


class CandidateEvidenceGateStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    BLOCKED = "BLOCKED"
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True, slots=True)
class TokenAuthorityEvidence:
    mint: str
    mint_authority: str | None
    freeze_authority: str | None
    observed_slot: int
    source_id: str
    evidence_id: str
    schema_version: str = "token_authority_evidence.v1"

    def __post_init__(self) -> None:
        _finalize_evidence(self, "token-authority-evidence")

    def identity_payload(self) -> dict[str, object]:
        return {
            "freeze_authority": self.freeze_authority,
            "mint": self.mint,
            "mint_authority": self.mint_authority,
            "observed_slot": self.observed_slot,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
        }


@dataclass(frozen=True, slots=True)
class HolderConcentrationEvidence:
    mint: str
    top_holders_bps: int
    holder_count: int
    observed_slot: int
    source_id: str
    evidence_id: str
    schema_version: str = "holder_concentration_evidence.v1"

    def __post_init__(self) -> None:
        _finalize_evidence(self, "holder-concentration-evidence")

    def identity_payload(self) -> dict[str, object]:
        return {
            "holder_count": self.holder_count,
            "mint": self.mint,
            "observed_slot": self.observed_slot,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
            "top_holders_bps": self.top_holders_bps,
        }


@dataclass(frozen=True, slots=True)
class LiquidityPoolEvidence:
    mint: str
    pool: str
    quote_mint: str
    base_reserve_raw: int
    quote_reserve_raw: int
    observed_slot: int
    source_id: str
    evidence_id: str
    schema_version: str = "liquidity_pool_evidence.v1"

    def __post_init__(self) -> None:
        _finalize_evidence(self, "liquidity-pool-evidence")

    def identity_payload(self) -> dict[str, object]:
        return {
            "base_reserve_raw": self.base_reserve_raw,
            "mint": self.mint,
            "observed_slot": self.observed_slot,
            "pool": self.pool,
            "quote_mint": self.quote_mint,
            "quote_reserve_raw": self.quote_reserve_raw,
            "schema_version": self.schema_version,
            "source_id": self.source_id,
        }


@dataclass(frozen=True, slots=True)
class TokenLifecycleRiskEvidence:
    mint: str
    lifecycle_id: str
    phase: str
    risk_codes: tuple[str, ...]
    evidence_id: str
    schema_version: str = "token_lifecycle_risk_evidence.v1"

    def __post_init__(self) -> None:
        _finalize_evidence(self, "token-lifecycle-risk-evidence")

    def identity_payload(self) -> dict[str, object]:
        return {
            "lifecycle_id": self.lifecycle_id,
            "mint": self.mint,
            "phase": self.phase,
            "risk_codes": self.risk_codes,
            "schema_version": self.schema_version,
        }


def _finalize_evidence(value, namespace: str):
    for name in value.identity_payload():
        field = getattr(value, name)
        if name.endswith("_raw") or name in {"observed_slot", "top_holders_bps", "holder_count"}:
            if isinstance(field, bool) or not isinstance(field, int) or field < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        elif name not in {"mint_authority", "freeze_authority", "risk_codes"} and (
            not isinstance(field, str) or not field.strip()
        ):
            raise ValueError(f"{name} must be non-empty")
    if hasattr(value, "top_holders_bps") and value.top_holders_bps > 10000:
        raise ValueError("top_holders_bps must be <= 10000")
    if hasattr(value, "risk_codes") and (
        not isinstance(value.risk_codes, tuple)
        or not all(isinstance(item, str) and item.strip() for item in value.risk_codes)
    ):
        raise ValueError("risk_codes must contain non-empty text")
    if value.evidence_id != deterministic_id(namespace, value.identity_payload()):
        raise ValueError("evidence_id does not match deterministic payload")


@dataclass(frozen=True, slots=True)
class CandidateSafetyFundingBinding:
    candidate_id: str
    wallet: str
    mint: str
    status: CandidateEvidenceGateStatus
    evidence_ids: tuple[str, ...]
    funding_edge_ids: tuple[str, ...]
    related_wallets: tuple[str, ...]
    reason_codes: tuple[str, ...]
    binding_id: str
    schema_version: str = "candidate_safety_funding_binding.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.status, CandidateEvidenceGateStatus):
            raise TypeError("status must be CandidateEvidenceGateStatus")
        for name in ("candidate_id", "wallet", "mint", "binding_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if self.status is CandidateEvidenceGateStatus.ELIGIBLE and self.reason_codes:
            raise ValueError("eligible binding cannot contain reason codes")
        if self.status is not CandidateEvidenceGateStatus.ELIGIBLE and not self.reason_codes:
            raise ValueError("non-eligible binding requires reason codes")
        if self.binding_id != deterministic_id(
            "candidate-safety-funding-binding", self.identity_payload()
        ):
            raise ValueError("binding_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "evidence_ids": self.evidence_ids,
            "funding_edge_ids": self.funding_edge_ids,
            "mint": self.mint,
            "reason_codes": self.reason_codes,
            "related_wallets": self.related_wallets,
            "schema_version": self.schema_version,
            "status": self.status.value,
            "wallet": self.wallet,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"binding_id": self.binding_id, **self.identity_payload()}


def bind_candidate_safety_funding(
    *,
    candidate_id: str,
    wallet: str,
    mint: str,
    authority: TokenAuthorityEvidence | None,
    concentration: HolderConcentrationEvidence | None,
    liquidity: LiquidityPoolEvidence | None,
    lifecycle: TokenLifecycleRiskEvidence | None,
    funding_edge_ids: tuple[str, ...] = (),
    related_wallets: tuple[str, ...] = (),
    max_concentration_bps: int = 5000,
    min_quote_reserve_raw: int = 1,
) -> CandidateSafetyFundingBinding:
    reasons: list[str] = []
    evidence = tuple(item for item in (authority, concentration, liquidity, lifecycle) if item is not None)
    if len(evidence) != 4:
        reasons.append("INCOMPLETE_SAFETY_EVIDENCE")
    if any(getattr(item, "mint", None) != mint.strip() for item in evidence):
        reasons.append("TOKEN_IDENTITY_MISMATCH")
    if authority is not None and authority.mint_authority is not None:
        reasons.append("MINT_AUTHORITY_ACTIVE")
    if authority is not None and authority.freeze_authority is not None:
        reasons.append("FREEZE_AUTHORITY_ACTIVE")
    if concentration is not None and concentration.top_holders_bps > max_concentration_bps:
        reasons.append("HOLDER_CONCENTRATION_HIGH")
    if liquidity is not None and liquidity.quote_reserve_raw < min_quote_reserve_raw:
        reasons.append("LIQUIDITY_INSUFFICIENT")
    if lifecycle is not None and lifecycle.risk_codes:
        reasons.extend(f"LIFECYCLE:{code}" for code in lifecycle.risk_codes)
    if not funding_edge_ids:
        reasons.append("FUNDING_PROVENANCE_INCOMPLETE")
    incomplete = any(code.endswith("INCOMPLETE") or code.startswith("INCOMPLETE_") for code in reasons)
    status = (
        CandidateEvidenceGateStatus.INCOMPLETE
        if incomplete
        else CandidateEvidenceGateStatus.BLOCKED
        if reasons
        else CandidateEvidenceGateStatus.ELIGIBLE
    )
    identity = {
        "candidate_id": candidate_id.strip(),
        "evidence_ids": tuple(sorted(item.evidence_id for item in evidence)),
        "funding_edge_ids": tuple(sorted(funding_edge_ids)),
        "mint": mint.strip(),
        "reason_codes": tuple(sorted(set(reasons))),
        "related_wallets": tuple(sorted(set(related_wallets))),
        "schema_version": "candidate_safety_funding_binding.v1",
        "status": status.value,
        "wallet": wallet.strip(),
    }
    return CandidateSafetyFundingBinding(
        status=status,
        binding_id=deterministic_id("candidate-safety-funding-binding", identity),
        **{key: value for key, value in identity.items() if key not in {"status", "schema_version"}},
    )


__all__ = [
    "CandidateEvidenceGateStatus",
    "CandidateSafetyFundingBinding",
    "HolderConcentrationEvidence",
    "LiquidityPoolEvidence",
    "TokenAuthorityEvidence",
    "TokenLifecycleRiskEvidence",
    "bind_candidate_safety_funding",
]
