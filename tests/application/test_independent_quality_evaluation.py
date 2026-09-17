import json
from pathlib import Path

import pytest

from smart_money.application.independent_quality_evaluation import (
    evaluate_independent_dataset,
)

FIXTURE = Path("fixtures/quality/independent-evaluation-v1.json")


def test_held_out_quality_metrics_include_safety_funding_and_route_coverage():
    report = evaluate_independent_dataset(json.loads(FIXTURE.read_text(encoding="utf-8")))
    assert (report.true_positive, report.false_positive, report.false_negative) == (2, 1, 1)
    assert (report.precision_bps, report.recall_bps) == (6666, 6666)
    assert (report.excluded_by_safety, report.excluded_by_funding) == (1, 1)
    assert set(report.coverage) == {"cyclic_route", "jupiter_route", "orca_whirlpool", "plain_transfer", "pump_launch", "raydium_amm", "raydium_cpmm"}
    assert report == evaluate_independent_dataset(json.loads(FIXTURE.read_text(encoding="utf-8")))


def test_quality_evaluation_rejects_training_split_and_duplicate_identity():
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    document["split"] = "training"
    with pytest.raises(ValueError, match="independent"):
        evaluate_independent_dataset(document)
    document["split"] = "evaluation"
    document["items"].append(document["items"][0])
    with pytest.raises(ValueError, match="unique"):
        evaluate_independent_dataset(document)
