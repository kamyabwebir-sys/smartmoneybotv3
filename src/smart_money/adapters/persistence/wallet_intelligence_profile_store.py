from __future__ import annotations

from smart_money.adapters.persistence.generic_value_store import (
    GenericValueStore,
    ValueStoreManifest,
)
from smart_money.application.wallet_intelligence_profile import (
    WalletIntelligenceProfile,
)

_SCHEMA_VERSION = "wallet_intelligence_profile_store.v1"


def _parse(data: dict[str, Any]) -> WalletIntelligenceProfile:
    return WalletIntelligenceProfile(
        wallet=data["wallet"],
        observation_count=data["observation_count"],
        observed_from_slot=data["observed_from_slot"],
        observed_to_slot=data["observed_to_slot"],
        activity_count=data["activity_count"],
        buy_count=data["buy_count"],
        sell_count=data["sell_count"],
        unknown_count=data["unknown_count"],
        distinct_token_observation_total=data["distinct_token_observation_total"],
        token_delta_total=data["token_delta_total"],
        native_delta_total=data["native_delta_total"],
        data_completeness_bps=data["data_completeness_bps"],
        observation_ids=tuple(data["observation_ids"]),
        profile_id=data["profile_id"],
        schema_version=data["schema_version"],
    )


_MANIFEST = ValueStoreManifest(
    schema_version=_SCHEMA_VERSION,
    value_key="profile",
    id_field="profile_id",
    parse=_parse,
    verify_canonical=True,
)


class JsonWalletIntelligenceProfileStore:
    def __init__(self, file_path: str | object) -> None:
        self._inner = GenericValueStore(file_path, _MANIFEST)

    def save(self, profile: WalletIntelligenceProfile) -> str:
        return self._inner.save(profile)

    def load(self) -> WalletIntelligenceProfile | None:
        return self._inner.load()


__all__ = ["JsonWalletIntelligenceProfileStore"]
