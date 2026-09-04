from __future__ import annotations

from smart_money.application.wallet_behavior_fingerprint import WalletBehaviorFingerprint
from smart_money.application.wallet_candidate_feature import WalletCandidateFeature
from smart_money.core.ids import deterministic_id


def bind_behavior_fingerprint_features(
    features: tuple[WalletCandidateFeature, ...],
    fingerprints: tuple[WalletBehaviorFingerprint, ...],
) -> tuple[WalletCandidateFeature, ...]:
    if not isinstance(features, tuple) or not all(
        isinstance(item, WalletCandidateFeature) for item in features
    ):
        raise TypeError("features must be a tuple of WalletCandidateFeature")
    if not isinstance(fingerprints, tuple) or not all(
        isinstance(item, WalletBehaviorFingerprint) for item in fingerprints
    ):
        raise TypeError("fingerprints must be a tuple of WalletBehaviorFingerprint")
    by_wallet: dict[str, WalletBehaviorFingerprint] = {}
    for fingerprint in fingerprints:
        wallet = fingerprint.wallet.strip()
        if wallet in by_wallet:
            raise ValueError(f"duplicate fingerprint for wallet: {wallet}")
        by_wallet[wallet] = fingerprint
    bound: list[WalletCandidateFeature] = []
    for feature in features:
        fingerprint = by_wallet.get(feature.wallet)
        identity = feature.identity_payload()
        if fingerprint is not None:
            if fingerprint.profile_id != feature.profile_id:
                raise ValueError(
                    f"fingerprint profile_id mismatch for wallet: {feature.wallet}"
                )
            identity["buy_ratio_bps"] = fingerprint.buy_ratio_bps
            identity["data_completeness_bps"] = fingerprint.data_completeness_bps
        bound.append(
            WalletCandidateFeature(
                **identity,
                feature_id=deterministic_id("wallet_candidate_feature", identity),
            )
        )
    return tuple(sorted(bound, key=lambda item: item.wallet))


__all__ = ["bind_behavior_fingerprint_features"]
