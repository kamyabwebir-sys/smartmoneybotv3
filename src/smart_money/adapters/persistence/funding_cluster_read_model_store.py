from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.funding_cluster_detection import FundingCluster
from smart_money.application.funding_cluster_read_model import (
    FundingClusterReadModel,
    FundingClusterReadRow,
)
from smart_money.application.wallet_relationship_evidence import WalletRelationshipEvidence
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "funding_cluster_read_model_store.v1"


class JsonFundingClusterReadModelStore:
    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._model: FundingClusterReadModel | None = None
        self._load()

    def save(self, model: FundingClusterReadModel) -> str:
        if not isinstance(model, FundingClusterReadModel):
            raise TypeError("model must be FundingClusterReadModel")
        if self._model is not None and self._model != model:
            raise RuntimeError("funding cluster read model identity collision")
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {"model": model.canonical_dict(), "schema_version": _SCHEMA_VERSION}
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)
        self._model = model
        return model.model_id

    def load(self) -> FundingClusterReadModel | None:
        return self._model

    def _load(self) -> None:
        if not self._file_path.is_file():
            return
        raw = self._file_path.read_text(encoding="utf-8")
        document: Any = json.loads(raw)
        if document.get("schema_version") != _SCHEMA_VERSION:
            raise ValueError("unsupported funding cluster read model store schema_version")
        data = document["model"]
        rows: list[FundingClusterReadRow] = []
        for row in data["rows"]:
            cluster = row["cluster"]
            cluster_obj = FundingCluster(
                wallets=tuple(cluster["wallets"]),
                relationship_ids=tuple(cluster["relationship_ids"]),
                cluster_id=cluster["cluster_id"],
                schema_version=cluster["schema_version"],
            )
            relations = tuple(
                WalletRelationshipEvidence(
                    source_wallet=item["source_wallet"],
                    target_wallet=item["target_wallet"],
                    relationship_type=item["relationship_type"],
                    path_id=item["path_id"],
                    edge_evidence_ids=tuple(item["edge_evidence_ids"]),
                    provenance=dict(item["provenance"]),
                    relationship_id=item["relationship_id"],
                    schema_version=item["schema_version"],
                )
                for item in row["relationships"]
            )
            rows.append(FundingClusterReadRow(cluster_obj, relations))
        model = FundingClusterReadModel(
            rows=tuple(rows),
            model_id=data["model_id"],
            schema_version=data["schema_version"],
        )
        if canonical_json(document) != raw:
            raise ValueError("funding cluster read model store is not canonical JSON")
        self._model = model


__all__ = ["JsonFundingClusterReadModelStore"]
