"""Leakage-resistant construction of time-separated mainnet evaluation datasets."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_mainnet_evaluation_dataset(
    discoveries: list[Mapping[str, Any]],
    outcomes: list[Mapping[str, Any]],
    *,
    dataset_id: str,
    horizon: str,
    training_candidate_ids: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    if not all(isinstance(value, str) and value.strip() for value in (dataset_id, horizon)):
        raise ValueError("dataset_id and horizon must be non-empty")
    outcome_index = {row.get("candidate_id"): row for row in outcomes if isinstance(row, Mapping)}
    if len(outcome_index) != len(outcomes):
        raise ValueError("outcomes require unique candidate identities")
    items = []
    for discovery in discoveries:
        candidate_id = discovery.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip() or candidate_id in training_candidate_ids:
            raise ValueError("evaluation candidates must be unique from training")
        outcome = outcome_index.get(candidate_id)
        if outcome is None:
            continue
        observed_at = discovery.get("observed_at_epoch")
        labelled_at = outcome.get("observed_at_epoch")
        if type(observed_at) is not int or type(labelled_at) is not int or labelled_at <= observed_at:
            raise ValueError("outcome must be observed strictly after candidate discovery")
        if discovery.get("chain") != "solana:mainnet-beta":
            raise ValueError("dataset accepts only Solana mainnet-beta evidence")
        item = {
            "candidate_id": candidate_id,
            "predicted": discovery.get("predicted"),
            "safety_passed": discovery.get("safety_passed"),
            "funding_verified": discovery.get("funding_verified"),
            "route": discovery.get("route"),
            "outcome": outcome.get("outcome"),
            "discovered_at_epoch": observed_at,
            "outcome_observed_at_epoch": labelled_at,
            "source_evidence_hash": discovery.get("source_evidence_hash"),
        }
        if not all(type(item[key]) is bool for key in ("predicted", "safety_passed", "funding_verified")):
            raise TypeError("discovery decision flags must be booleans")
        if not all(isinstance(item[key], str) and item[key].strip() for key in ("route", "outcome", "source_evidence_hash")):
            raise ValueError("route, outcome and source evidence hash are required")
        items.append(item)
    if not items:
        raise ValueError("no time-separated labelled mainnet candidates")
    ids = [item["candidate_id"] for item in items]
    if len(set(ids)) != len(ids):
        raise ValueError("discoveries require unique candidate identities")
    return {
        "schema_version": "candidate_evaluation_dataset.v1", "split": "evaluation",
        "dataset_id": dataset_id.strip(), "horizon": horizon.strip(),
        "items": sorted(items, key=lambda item: item["candidate_id"]),
        "provenance": {"chain": "solana:mainnet-beta", "time_separated": True,
                       "training_overlap_count": 0},
    }


__all__ = ["build_mainnet_evaluation_dataset"]
