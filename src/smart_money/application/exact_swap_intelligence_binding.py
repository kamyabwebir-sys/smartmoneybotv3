"""Bind exact swap evidence into existing deterministic wallet intelligence models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from smart_money.application.early_entry_consistency import (
    EarlyEntryConsistency,
    evaluate_early_entry_consistency,
)
from smart_money.application.exact_swap_attribution import (
    ExactSwapAttribution,
    project_exact_attribution_activity,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_wallet_activity_aggregation import (
    aggregate_solana_wallet_activity,
)
from smart_money.application.solana_wallet_token_activity_ledger import (
    ingest_solana_wallet_token_activity,
)
from smart_money.application.solana_wallet_token_activity_query import (
    query_solana_wallet_token_activity,
)
from smart_money.application.wallet_behavior_fingerprint import (
    WalletBehaviorFingerprint,
    project_wallet_behavior_fingerprint,
)
from smart_money.application.wallet_candidate_evidence import (
    WalletCandidateEvidence,
    build_wallet_candidate_evidence,
)
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.application.wallet_intelligence_ledger import (
    ingest_wallet_intelligence_observation,
)
from smart_money.application.wallet_intelligence_profile import (
    WalletIntelligenceProfile,
    project_wallet_intelligence_profiles,
)
from smart_money.application.wallet_intelligence_projection import (
    project_wallet_activity_to_intelligence,
)
from smart_money.application.wallet_intelligence_read_model import (
    build_wallet_intelligence_read_model,
)
from smart_money.application.wallet_ranking import WalletRanking, rank_wallet_candidates
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class ExactSwapIntelligenceBinding:
    wallet: str
    attribution_ids: tuple[str, ...]
    profile: WalletIntelligenceProfile
    fingerprint: WalletBehaviorFingerprint
    early_entry: EarlyEntryConsistency
    candidate_evidence: WalletCandidateEvidence
    ranking: WalletRanking
    token_lifecycle_ids: tuple[str, ...]
    binding_id: str
    schema_version: str = "exact_swap_intelligence_binding.v1"

    def canonical_dict(self) -> dict[str, object]:
        return {
            "attribution_ids": self.attribution_ids,
            "binding_id": self.binding_id,
            "candidate_evidence": self.candidate_evidence.canonical_dict(),
            "early_entry": self.early_entry.canonical_dict(),
            "fingerprint": self.fingerprint.canonical_dict(),
            "profile": self.profile.canonical_dict(),
            "ranking": self.ranking.canonical_dict(),
            "schema_version": self.schema_version,
            "token_lifecycle_ids": self.token_lifecycle_ids,
            "wallet": self.wallet,
        }


def bind_exact_swaps_to_intelligence(
    attributions: tuple[ExactSwapAttribution, ...],
    ledger: EvidenceLedger,
    *,
    reference_slots: Mapping[str, int],
    relationship_count: int = 0,
    cohort_count: int = 0,
    token_lifecycle_ids: Mapping[str, str] | None = None,
) -> ExactSwapIntelligenceBinding:
    if not attributions or not all(
        isinstance(item, ExactSwapAttribution) for item in attributions
    ):
        raise TypeError("attributions must be a non-empty tuple")
    wallet = attributions[0].wallet
    if any(item.wallet != wallet or item.suppressed for item in attributions):
        raise ValueError("attributions must be unsuppressed and share one wallet")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in (relationship_count, cohort_count)
    ):
        raise ValueError("relationship and cohort counts must be non-negative integers")
    lifecycle = token_lifecycle_ids or {}
    if not isinstance(lifecycle, Mapping):
        raise TypeError("token_lifecycle_ids must be a mapping")
    for attribution in sorted(
        attributions, key=lambda item: (item.slot, item.signature, item.attribution_id)
    ):
        ingest_solana_wallet_token_activity(
            project_exact_attribution_activity(attribution), ledger
        )
    aggregate = aggregate_solana_wallet_activity(ledger, wallet=wallet)
    observation = project_wallet_activity_to_intelligence(aggregate)
    ingest_wallet_intelligence_observation(observation, ledger)
    profiles = project_wallet_intelligence_profiles(
        build_wallet_intelligence_read_model(ledger)
    )
    profile = next(item for item in profiles if item.wallet == wallet)
    fingerprint = project_wallet_behavior_fingerprint(profile)
    activities = query_solana_wallet_token_activity(ledger, wallet=wallet).activities
    early_entry = evaluate_early_entry_consistency(
        activities, reference_slots=reference_slots
    )
    bound_lifecycle_ids = tuple(
        sorted(
            lifecycle[item.asset_mint].strip()
            for item in attributions
            if item.asset_mint in lifecycle
            and isinstance(lifecycle[item.asset_mint], str)
            and lifecycle[item.asset_mint].strip()
        )
    )
    feature_identity = {
        "activity_count": profile.activity_count,
        "buy_ratio_bps": fingerprint.buy_ratio_bps,
        "cohort_count": cohort_count,
        "data_completeness_bps": fingerprint.data_completeness_bps,
        "early_entry_consistency_bps": early_entry.consistency_bps,
        "profile_id": profile.profile_id,
        "relationship_count": relationship_count,
        "schema_version": "wallet_candidate_feature.v1",
        "wallet": wallet,
    }
    feature = WalletCandidateFeature(
        feature_id=deterministic_id("wallet_candidate_feature", feature_identity),
        **feature_identity,
    )
    provenance = {
        "attribution_ids": ",".join(sorted(item.attribution_id for item in attributions)),
        "fingerprint_id": fingerprint.fingerprint_id,
        "profile_id": profile.profile_id,
    }
    if bound_lifecycle_ids:
        provenance["token_lifecycle_ids"] = ",".join(bound_lifecycle_ids)
    candidate = build_wallet_candidate_evidence(feature, provenance=provenance)
    ranking = rank_wallet_candidates((candidate,))
    identity = {
        "attribution_ids": tuple(sorted(item.attribution_id for item in attributions)),
        "candidate_evidence_id": candidate.evidence_id,
        "early_entry_id": early_entry.consistency_id,
        "fingerprint_id": fingerprint.fingerprint_id,
        "profile_id": profile.profile_id,
        "ranking_id": ranking.ranking_id,
        "schema_version": "exact_swap_intelligence_binding.v1",
        "token_lifecycle_ids": bound_lifecycle_ids,
        "wallet": wallet,
    }
    return ExactSwapIntelligenceBinding(
        wallet=wallet,
        attribution_ids=identity["attribution_ids"],
        profile=profile,
        fingerprint=fingerprint,
        early_entry=early_entry,
        candidate_evidence=candidate,
        ranking=ranking,
        token_lifecycle_ids=bound_lifecycle_ids,
        binding_id=deterministic_id("exact-swap-intelligence-binding", identity),
    )


__all__ = ["ExactSwapIntelligenceBinding", "bind_exact_swaps_to_intelligence"]
