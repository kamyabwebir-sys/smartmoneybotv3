from __future__ import annotations

from typing import Any

from smart_money.adapters.persistence.generic_collection_store import (
    GenericCollectionStore,
    StoreManifest,
)
from smart_money.application.wallet_relationship_intelligence import (
    WalletRelationshipIntelligence,
)

_SCHEMA_VERSION = "wallet_relationship_intelligence_store.v1"


def _parse(data: dict[str, Any]) -> WalletRelationshipIntelligence:
    return WalletRelationshipIntelligence(
        cluster_id=data["cluster_id"],
        intelligence_id=data["intelligence_id"],
        relationship_count=data["relationship_count"],
        relationship_ids=tuple(data["relationship_ids"]),
        schema_version=data.get("schema_version", _SCHEMA_VERSION),
        wallets=tuple(data["wallets"]),
    )


_MANIFEST = StoreManifest(
    schema_version=_SCHEMA_VERSION,
    collection_key="models",
    id_field="intelligence_id",
    parse=_parse,
    verify_canonical=True,
)


class JsonWalletRelationshipIntelligenceStore:
    def __init__(self, file_path: str | Any) -> None:
        self._inner = GenericCollectionStore(file_path, _MANIFEST)

    def append(self, model: WalletRelationshipIntelligence) -> str:
        return self._inner.append(model)

    def get(self, intelligence_id: str) -> WalletRelationshipIntelligence | None:
        return self._inner.get(intelligence_id)

    def iter_models(self):  # type: ignore[override]
        return self._inner.iter_items()

    @property
    def model_count(self) -> int:
        return self._inner.count


__all__ = ["JsonWalletRelationshipIntelligenceStore"]
