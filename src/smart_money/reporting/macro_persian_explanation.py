from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.analytics.macro_context_binding import AnalyticsSubjectKind
from smart_money.analytics.macro_context_projection import MacroContextStatus
from smart_money.analytics.macro_context_read_model import MacroContextReadModel
from smart_money.core.ids import deterministic_id

_KIND_LABELS = {
    AnalyticsSubjectKind.TOKEN: "توکن",
    AnalyticsSubjectKind.WALLET: "ولت",
}


@dataclass(frozen=True, slots=True)
class PersianMacroExplanation:
    """Deterministic Persian explanation of macro context evidence."""

    subject_kind: AnalyticsSubjectKind
    subject_id: str
    status: MacroContextStatus
    summary: str
    detail: str
    provenance: str
    schema_version: str = "persian_macro_explanation.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.subject_kind, AnalyticsSubjectKind):
            raise TypeError("subject_kind must be an AnalyticsSubjectKind")
        for field_name in ("subject_id", "summary", "detail", "provenance"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not isinstance(self.status, MacroContextStatus):
            raise TypeError("status must be a MacroContextStatus")
        if self.schema_version != "persian_macro_explanation.v1":
            raise ValueError("unsupported Persian explanation schema_version")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "detail": self.detail,
            "provenance": self.provenance,
            "schema_version": self.schema_version,
            "status": self.status,
            "subject_id": self.subject_id,
            "subject_kind": self.subject_kind,
            "summary": self.summary,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id(
            "persian_macro_explanation",
            self.canonical_dict(),
        )


def explain_macro_context(
    model: MacroContextReadModel,
) -> PersianMacroExplanation:
    """Render a read model into Persian evidence language, never a verdict."""
    if not isinstance(model, MacroContextReadModel):
        raise TypeError("model must be a MacroContextReadModel")
    kind = _KIND_LABELS[model.subject_kind]
    if model.context_status is MacroContextStatus.MISSING:
        summary = f"برای {kind} «{model.subject_id}» دادهٔ کلان معتبری در این بازه پیدا نشد."
        detail = (
            f"شاخص «{model.metric}» در پنجرهٔ انتخاب‌شده مشاهده‌ای ندارد؛ "
            "بنابراین دربارهٔ اثر وضعیت کلان بر این مورد نتیجه‌گیری نمی‌شود."
        )
    elif model.context_status is MacroContextStatus.CONFLICTED:
        summary = f"برای {kind} «{model.subject_id}» بین شواهد کلان تضاد وجود دارد."
        detail = (
            f"در شاخص «{model.metric}»، تعداد {model.conflicted_count} مشاهده "
            "متناقض ثبت شده است؛ این context برای نتیجه‌گیری قطعی مناسب نیست."
        )
    else:
        summary = f"برای {kind} «{model.subject_id}» context کلان ثبت شده است."
        detail = (
            f"شاخص «{model.metric}» دارای {model.observation_count} مشاهده است "
            f"و وضعیت فعلی آن «{model.context_status.value}» است."
        )
        if model.latest_observed_at is not None:
            detail += (
                f" آخرین مشاهده در زمان {model.latest_observed_at} با مقدار "
                f"{model.latest_value} {model.latest_unit or ''} ثبت شده است."
            )
    provenance = (
        f"منبع: {model.latest_source_id or 'نامشخص'}؛ "
        f"نسخهٔ منبع: {model.latest_source_revision or 'نامشخص'}؛ "
        "این داده external evidence است و به‌تنهایی توصیهٔ خرید یا فروش نیست."
    )
    return PersianMacroExplanation(
        subject_kind=model.subject_kind,
        subject_id=model.subject_id,
        status=model.context_status,
        summary=summary,
        detail=detail,
        provenance=provenance,
    )


__all__ = ["PersianMacroExplanation", "explain_macro_context"]
