from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from smart_money.analytics.macro_context_projection import MacroAnalyticsContext
from smart_money.core.ids import deterministic_id


class AnalyticsSubjectKind(str, Enum):
    TOKEN = "TOKEN"
    WALLET = "WALLET"


@dataclass(frozen=True, slots=True)
class MacroContextBinding:
    """Non-decisional link between macro context and an Analytics subject."""

    subject_kind: AnalyticsSubjectKind
    subject_id: str
    context: MacroAnalyticsContext
    schema_version: str = "macro_context_binding.v1"

    def __post_init__(self) -> None:
        if not isinstance(self.subject_kind, AnalyticsSubjectKind):
            raise TypeError("subject_kind must be an AnalyticsSubjectKind")
        if not isinstance(self.subject_id, str) or not self.subject_id.strip():
            raise ValueError("subject_id must be a non-empty string")
        object.__setattr__(self, "subject_id", self.subject_id.strip())
        if not isinstance(self.context, MacroAnalyticsContext):
            raise TypeError("context must be a MacroAnalyticsContext")
        if self.schema_version != "macro_context_binding.v1":
            raise ValueError("unsupported macro context binding schema_version")

    @classmethod
    def for_token(
        cls,
        token_id: str,
        context: MacroAnalyticsContext,
    ) -> MacroContextBinding:
        return cls(
            subject_kind=AnalyticsSubjectKind.TOKEN,
            subject_id=token_id,
            context=context,
        )

    @classmethod
    def for_wallet(
        cls,
        wallet_id: str,
        context: MacroAnalyticsContext,
    ) -> MacroContextBinding:
        return cls(
            subject_kind=AnalyticsSubjectKind.WALLET,
            subject_id=wallet_id,
            context=context,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.canonical_dict(),
            "schema_version": self.schema_version,
            "subject_id": self.subject_id,
            "subject_kind": self.subject_kind,
        }

    @property
    def canonical_id(self) -> str:
        return deterministic_id("macro_context_binding", self.canonical_dict())


__all__ = ["AnalyticsSubjectKind", "MacroContextBinding"]
