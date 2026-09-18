from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from smart_money.analytics.macro_context_binding import (
    AnalyticsSubjectKind,
    MacroContextBinding,
)
from smart_money.analytics.macro_context_projection import (
    MacroAnalyticsContext,
    MacroContextStatus,
)
from smart_money.domain.macro_context import (
    MacroEvidenceObservation,
    MacroObservationStatus,
)


def _context() -> MacroAnalyticsContext:
    observation = MacroEvidenceObservation(
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
        latest_observation=observation,
        status=MacroContextStatus.PROVISIONAL,
        observation_count=1,
        conflicted_count=0,
        unknown_count=0,
    )


def test_binding_supports_token_and_wallet_without_scoring() -> None:
    token = MacroContextBinding.for_token("evm:base:token-1", _context())
    wallet = MacroContextBinding.for_wallet("evm:base:wallet-1", _context())

    assert token.subject_kind is AnalyticsSubjectKind.TOKEN
    assert wallet.subject_kind is AnalyticsSubjectKind.WALLET
    assert token.canonical_id != wallet.canonical_id
    assert token.context.canonical_id == wallet.context.canonical_id
    assert not hasattr(token, "__dict__")
    with pytest.raises(FrozenInstanceError):
        token.subject_id = "changed"  # type: ignore[misc]


def test_binding_is_deterministic_for_same_subject_and_context() -> None:
    left = MacroContextBinding.for_token("token-1", _context())
    right = MacroContextBinding.for_token("token-1", _context())

    assert left.canonical_dict() == right.canonical_dict()
    assert left.canonical_id == right.canonical_id


@pytest.mark.parametrize(
    ("kind", "subject_id", "error"),
    [
        ("TOKEN", "token-1", "AnalyticsSubjectKind"),
        (AnalyticsSubjectKind.TOKEN, "", "subject_id"),
    ],
)
def test_binding_fails_closed(
    kind: object,
    subject_id: str,
    error: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=error):
        MacroContextBinding(
            subject_kind=kind,
            subject_id=subject_id,
            context=_context(),
        )
