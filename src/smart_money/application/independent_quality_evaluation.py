"""Deterministic candidate evaluation on a held-out, explicitly labelled corpus."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from smart_money.application.candidate_quality import (
    CandidateLabel,
    analyze_precision_recall,
    build_candidate_quality_label,
)
from smart_money.core.ids import deterministic_id


@dataclass(frozen=True, slots=True)
class QualityEvaluationReport:
    dataset_id: str
    horizon: str
    sample_count: int
    eligible_prediction_count: int
    excluded_by_safety: int
    excluded_by_funding: int
    precision_bps: int
    recall_bps: int
    true_positive: int
    false_positive: int
    false_negative: int
    coverage: tuple[str, ...]
    report_id: str
    schema_version: str = "independent_quality_evaluation.v1"

    def canonical_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_independent_dataset(document: Mapping[str, Any]) -> QualityEvaluationReport:
    if not isinstance(document, Mapping) or document.get("schema_version") != "candidate_evaluation_dataset.v1":
        raise ValueError("unsupported evaluation dataset")
    if document.get("split") != "evaluation":
        raise ValueError("quality metrics require the independent evaluation split")
    dataset_id, horizon = document.get("dataset_id"), document.get("horizon")
    if not all(isinstance(value, str) and value.strip() for value in (dataset_id, horizon)):
        raise ValueError("dataset_id and horizon must be non-empty")
    rows = document.get("items")
    if not isinstance(rows, list) or not rows:
        raise ValueError("evaluation items must be a non-empty list")
    labels, predicted, seen, coverage = [], [], set(), set()
    excluded_safety = excluded_funding = 0
    for row in rows:
        if not isinstance(row, Mapping):
            raise TypeError("evaluation row must be an object")
        candidate_id = row.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip() or candidate_id in seen:
            raise ValueError("candidate_id must be unique and non-empty")
        seen.add(candidate_id)
        try:
            label = CandidateLabel(row.get("outcome"))
        except ValueError as exc:
            raise ValueError("unsupported candidate outcome") from exc
        labels.append(build_candidate_quality_label(candidate_id, f"{dataset_id}:{candidate_id}", horizon, label, "held-out outcome label"))
        route = row.get("route")
        if not isinstance(route, str) or not route.strip():
            raise ValueError("route coverage must be non-empty")
        coverage.add(route.strip())
        selected = row.get("predicted")
        safety = row.get("safety_passed")
        funding = row.get("funding_verified")
        if not all(type(value) is bool for value in (selected, safety, funding)):
            raise TypeError("prediction, safety and funding flags must be booleans")
        if selected and not safety:
            excluded_safety += 1
        if selected and safety and not funding:
            excluded_funding += 1
        if selected and safety and funding:
            predicted.append(candidate_id)
    metrics = analyze_precision_recall(tuple(labels), tuple(predicted), horizon)
    identity = {
        "coverage": tuple(sorted(coverage)), "dataset_id": dataset_id, "horizon": horizon,
        "label_ids": tuple(label.label_id for label in labels), "predicted": tuple(sorted(predicted)),
        "schema_version": "independent_quality_evaluation.v1",
    }
    return QualityEvaluationReport(
        dataset_id, horizon, len(rows), len(predicted), excluded_safety, excluded_funding,
        metrics.precision_bps, metrics.recall_bps, metrics.true_positive,
        metrics.false_positive, metrics.false_negative, tuple(sorted(coverage)),
        deterministic_id("independent-quality-evaluation", identity),
    )


__all__ = ["QualityEvaluationReport", "evaluate_independent_dataset"]
