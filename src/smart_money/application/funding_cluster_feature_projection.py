from __future__ import annotations

from smart_money.application.funding_cluster_detection import FundingCluster
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id


def project_funding_cluster_features(
    cluster: FundingCluster,
    *,
    profile_ids: dict[str, str],
    cohort_count: int = 0,
    early_entry_consistency_bps: dict[str, int] | None = None,
) -> tuple[WalletCandidateFeature, ...]:
    if not isinstance(cluster, FundingCluster):
        raise TypeError("cluster must be FundingCluster")
    if not isinstance(profile_ids, dict):
        raise TypeError("profile_ids must be a dict")
    if isinstance(cohort_count, bool) or not isinstance(cohort_count, int) or cohort_count < 0:
        raise ValueError("cohort_count must be a non-negative integer")
    consistency = early_entry_consistency_bps or {}
    if not isinstance(consistency, dict):
        raise TypeError("early_entry_consistency_bps must be a dict")
    features: list[WalletCandidateFeature] = []
    for wallet in cluster.wallets:
        profile_id = profile_ids.get(wallet)
        if not isinstance(profile_id, str) or not profile_id.strip():
            raise ValueError(f"missing profile_id for wallet: {wallet}")
        consistency_bps = consistency.get(wallet, 0)
        identity = {
            "activity_count": 0,
            "buy_ratio_bps": 0,
            "cohort_count": cohort_count,
            "data_completeness_bps": 0,
            "early_entry_consistency_bps": consistency_bps,
            "profile_id": profile_id.strip(),
            "relationship_count": len(cluster.relationship_ids),
            "schema_version": "wallet_candidate_feature.v1",
            "wallet": wallet.strip(),
        }
        features.append(
            WalletCandidateFeature(
                **identity,
                feature_id=deterministic_id("wallet_candidate_feature", identity),
            )
        )
    return tuple(sorted(features, key=lambda item: item.wallet))


__all__ = ["project_funding_cluster_features"]
