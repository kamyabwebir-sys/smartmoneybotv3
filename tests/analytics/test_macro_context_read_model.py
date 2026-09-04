from decimal import Decimal

import pytest

from smart_money.analytics.macro_context_binding import MacroContextBinding
from smart_money.analytics.macro_context_projection import (
    MacroAnalyticsContext,
    MacroContextStatus,
)
from smart_money.analytics.macro_context_read_model import MacroContextReadModel
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)


def _context(
    status: MacroContextStatus = MacroContextStatus.PROVISIONAL,
    *,
    missing: bool = False,
) -> MacroAnalyticsContext:
    latest = None
    if not missing:
        latest = MacroEvidenceObservation(
            source_id="worldmonitor",
            metric="risk_sentiment",
            observed_at=10,
            value=Decimal("0.25"),
            unit="index",
            status=MacroObservationStatus.PROVISIONAL,
            source_revision="r1",
        )
    return MacroAnalyticsContext(
        metric="risk_sentiment",
        start_at=0,
        end_at=10,
        latest_observation=latest,
        status=status,
        observation_count=0 if missing else 1,
        conflicted_count=1 if status is MacroContextStatus.CONFLICTED else 0,
        unknown_count=0,
    )


def test_read_model_projects_token_context_and_provenance() -> None:
    binding = MacroContextBinding.for_token(
        "evm:base:token-1",
        _context(),
    )
    model = MacroContextReadModel.from_binding(binding)

    assert model.subject_id == "evm:base:token-1"
    assert model.latest_value == Decimal("0.25")
    assert model.latest_source_id == "worldmonitor"
    assert model.explanation_code == "MACRO_CONTEXT_AVAILABLE"
    assert model.missing is False
    assert model.conflicted is False


@pytest.mark.parametrize(
    ("status", "missing", "code"),
    [
        (MacroContextStatus.MISSING, True, "MACRO_CONTEXT_MISSING"),
        (MacroContextStatus.CONFLICTED, False, "MACRO_CONTEXT_CONFLICTED"),
    ],
)
def test_read_model_reports_missing_or_conflicted_context(
    status: MacroContextStatus,
    missing: bool,
    code: str,
) -> None:
    binding = MacroContextBinding.for_wallet(
        "evm:base:wallet-1",
        _context(status, missing=missing),
    )
    model = MacroContextReadModel.from_binding(binding)

    assert model.explanation_code == code
    assert model.missing is (status is MacroContextStatus.MISSING)
    assert model.conflicted is (status is MacroContextStatus.CONFLICTED)
    assert model.latest_observed_at is None if missing else True


def test_read_model_is_deterministic() -> None:
    left = MacroContextReadModel.from_binding(
        MacroContextBinding.for_wallet("wallet-1", _context())
    )
    right = MacroContextReadModel.from_binding(
        MacroContextBinding.for_wallet("wallet-1", _context())
    )

    assert left.canonical_dict() == right.canonical_dict()
    assert left.canonical_id == right.canonical_id
