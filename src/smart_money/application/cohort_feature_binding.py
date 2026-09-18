from __future__ import annotations

from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.application.wallet_cohort_detection import WalletCohort
from smart_money.core.ids import deterministic_id


def bind_cohort_features(
    features: tuple[WalletCandidateFeature, ...],
    cohorts: tuple[WalletCohort, ...],
) -> tuple[WalletCandidateFeature, ...]:
    if not isinstance(features, tuple) or not all(
        isinstance(item, WalletCandidateFeature) for item in features
    ):
        raise TypeError("features must be a tuple of WalletCandidateFeature")
    if not isinstance(cohorts, tuple) or not all(
        isinstance(item, WalletCohort) for item in cohorts
    ):
        raise TypeError("cohorts must be a tuple of WalletCohort")
    counts: dict[str, int] = {}
    for cohort in cohorts:
        for wallet in cohort.wallets:
            counts[wallet] = counts.get(wallet, 0) + 1
    bound: list[WalletCandidateFeature] = []
    for feature in features:
        identity = feature.identity_payload()
        identity["cohort_count"] = counts.get(feature.wallet, 0)
        bound.append(
            WalletCandidateFeature(
                **identity,
                feature_id=deterministic_id("wallet_candidate_feature", identity),
            )
        )
    return tuple(sorted(bound, key=lambda item: item.wallet))


__all__ = ["bind_cohort_features"]
