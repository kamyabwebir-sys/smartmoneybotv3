from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.analytics.macro_context_read_model import MacroContextReadModel
from smart_money.core.ids import deterministic_id
from smart_money.reporting.macro_persian_explanation import (
    PersianMacroExplanation,
    explain_macro_context,
)

_REPORT_SCHEMA_VERSION = "persian_macro_markdown_report.v1"


def _cell(value: object) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r\n", "<br>")
        .replace("\n", "<br>")
        .replace("\r", "<br>")
    )


@dataclass(frozen=True, slots=True)
class PersianMacroMarkdownReport:
    """Canonical Markdown report for one Token/Wallet macro context."""

    model_id: str
    explanation_id: str
    subject_id: str
    markdown: str
    schema_version: str = _REPORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "model_id",
            "explanation_id",
            "subject_id",
            "markdown",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if self.schema_version != _REPORT_SCHEMA_VERSION:
            raise ValueError("unsupported Persian Markdown report schema_version")

    @property
    def report_id(self) -> str:
        return deterministic_id(
            "persian_macro_markdown_report",
            {
                "explanation_id": self.explanation_id,
                "markdown": self.markdown,
                "model_id": self.model_id,
                "schema_version": self.schema_version,
                "subject_id": self.subject_id,
            },
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "markdown": self.markdown,
            "model_id": self.model_id,
            "report_id": self.report_id,
            "schema_version": self.schema_version,
            "subject_id": self.subject_id,
        }


def render_persian_macro_markdown(
    model: MacroContextReadModel,
) -> PersianMacroMarkdownReport:
    """Render a deterministic, evidence-only Persian Markdown report."""
    if not isinstance(model, MacroContextReadModel):
        raise TypeError("model must be a MacroContextReadModel")
    explanation: PersianMacroExplanation = explain_macro_context(model)
    latest_value = (
        "—" if model.latest_value is None else _cell(model.latest_value)
    )
    latest_unit = "—" if model.latest_unit is None else _cell(model.latest_unit)
    latest_time = (
        "—"
        if model.latest_observed_at is None
        else _cell(model.latest_observed_at)
    )
    lines = [
        "# گزارش فارسی وضعیت کلان",
        "",
        f"- نسخه گزارش: `{_REPORT_SCHEMA_VERSION}`",
        f"- شناسه گزارش Read Model: `{model.canonical_id}`",
        f"- شناسه توضیح: `{explanation.canonical_id}`",
        f"- نوع موضوع: `{_cell(model.subject_kind.value)}`",
        f"- شناسه موضوع: `{_cell(model.subject_id)}`",
        "",
        "## خلاصه",
        "",
        explanation.summary,
        "",
        "## توضیح تحلیلی",
        "",
        explanation.detail,
        "",
        "## آخرین مشاهده",
        "",
        "| شاخص | وضعیت | زمان مشاهده | مقدار | واحد |",
        "|---|---|---:|---:|---|",
        (
            f"| {_cell(model.metric)} | {_cell(model.context_status.value)} | "
            f"{latest_time} | {latest_value} | {latest_unit} |"
        ),
        "",
        "## کیفیت و پوشش داده",
        "",
        "| مورد | مقدار |",
        "|---|---:|",
        f"| تعداد مشاهده‌ها | {model.observation_count} |",
        f"| تعداد موارد متناقض | {model.conflicted_count} |",
        f"| تعداد موارد نامشخص | {model.unknown_count} |",
        f"| کد توضیح | `{_cell(model.explanation_code)}` |",
        "",
        "## منشأ داده",
        "",
        explanation.provenance,
        "",
        (
            "_این گزارش فقط نمایش deterministic شواهد خارجی است؛ "
            "توصیهٔ خرید، فروش یا محاسبهٔ ریسک نیست._"
        ),
        "",
    ]
    markdown = "\n".join(lines)
    return PersianMacroMarkdownReport(
        model_id=model.canonical_id,
        explanation_id=explanation.canonical_id,
        subject_id=model.subject_id,
        markdown=markdown,
    )


__all__ = [
    "PersianMacroMarkdownReport",
    "render_persian_macro_markdown",
]
