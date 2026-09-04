from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_candidate_evidence import WalletCandidateEvidence
from smart_money.application.wallet_candidate_read_model import WalletCandidateReadRow
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_candidate_persian_explanation.v1"


@dataclass(frozen=True, slots=True)
class PersianWalletCandidateExplanation:
    wallet: str
    summary: str
    detail: str
    provenance: str
    explanation_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("wallet", "summary", "detail", "provenance", "explanation_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet candidate explanation schema_version")
        if self.explanation_id != deterministic_id(
            "wallet_candidate_persian_explanation", self.identity_payload()
        ):
            raise ValueError("explanation_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "detail": self.detail,
            "provenance": self.provenance,
            "schema_version": self.schema_version,
            "summary": self.summary,
            "wallet": self.wallet.strip(),
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"explanation_id": self.explanation_id, **self.identity_payload()}


def explain_wallet_candidate(
    row: WalletCandidateReadRow,
) -> PersianWalletCandidateExplanation:
    if not isinstance(row, WalletCandidateReadRow):
        raise TypeError("row must be WalletCandidateReadRow")
    evidence: WalletCandidateEvidence = row.evidence
    feature = evidence.feature
    rank_text = f"رتبهٔ {row.ranking.rank}" if row.ranking is not None else "بدون رتبه"
    score_text = (
        f"امتیاز {row.ranking.score_bps} واحد پایه"
        if row.ranking is not None
        else "امتیاز رتبه‌بندی ثبت نشده"
    )
    status_text = "پیشنهادشده" if evidence.status.value == "PROPOSED" else "شواهد ناکافی"
    summary = f"ولت «{feature.wallet}» در وضعیت {status_text} قرار دارد؛ {rank_text}، {score_text}."
    detail = (
        f"تعداد فعالیت: {feature.activity_count}؛ نسبت خرید: {feature.buy_ratio_bps} واحد پایه؛ "
        f"ثبات ورود زودهنگام: {feature.early_entry_consistency_bps} واحد پایه؛ "
        f"تعداد ارتباط‌ها: {feature.relationship_count}؛ تعداد cohort: {feature.cohort_count}؛ "
        f"کامل‌بودن داده: {feature.data_completeness_bps} واحد پایه. "
        f"کدهای شواهد: {', '.join(evidence.reason_codes)}."
    )
    provenance = (
        f"منبع شواهد: {', '.join(f'{key}={value}' for key, value in sorted(evidence.provenance.items()))}. "
        "این توضیح صرفاً خلاصهٔ evidence است و توصیهٔ خرید یا فروش نیست."
    )
    identity = {
        "detail": detail,
        "provenance": provenance,
        "schema_version": _SCHEMA_VERSION,
        "summary": summary,
        "wallet": feature.wallet.strip(),
    }
    return PersianWalletCandidateExplanation(
        **identity,
        explanation_id=deterministic_id(
            "wallet_candidate_persian_explanation", identity
        ),
    )


__all__ = ["PersianWalletCandidateExplanation", "explain_wallet_candidate"]
