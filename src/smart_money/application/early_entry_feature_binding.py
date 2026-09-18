from __future__ import annotations

from smart_money.application.early_entry_consistency import EarlyEntryConsistency
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id


def bind_early_entry_features(
    features: tuple[WalletCandidateFeature, ...],
    consistencies: tuple[EarlyEntryConsistency, ...],
) -> tuple[WalletCandidateFeature, ...]:
    if not isinstance(features, tuple) or not all(
        isinstance(item, WalletCandidateFeature) for item in features
    ):
        raise TypeError("features must be a tuple of WalletCandidateFeature")
    if not isinstance(consistencies, tuple) or not all(
        isinstance(item, EarlyEntryConsistency) for item in consistencies
    ):
        raise TypeError("consistencies must be a tuple of EarlyEntryConsistency")
    values = {item.wallet.strip(): item.consistency_bps for item in consistencies}
    bound: list[WalletCandidateFeature] = []
    for feature in features:
        identity = feature.identity_payload()
        identity["early_entry_consistency_bps"] = values.get(feature.wallet, 0)
        bound.append(
            WalletCandidateFeature(
                **identity,
                feature_id=deterministic_id("wallet_candidate_feature", identity),
            )
        )
    return tuple(sorted(bound, key=lambda item: item.wallet))


__all__ = ["bind_early_entry_features"]
