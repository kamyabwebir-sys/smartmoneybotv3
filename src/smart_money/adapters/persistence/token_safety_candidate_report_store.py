from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from smart_money.adapters.persistence.atomic_file import atomic_replace
from smart_money.application.solana_candidate_discovery import SolanaWalletTokenCandidate
from smart_money.application.token_safety_candidate_binding import TokenSafetyCandidateBinding
from smart_money.application.token_safety_candidate_read_model import TokenSafetyCandidateReadRow
from smart_money.application.token_safety_candidate_report import TokenSafetyCandidateEvidenceReport
from smart_money.core.serialization import canonical_json

_SCHEMA_VERSION = "token_safety_candidate_evidence_report_store.v1"


class JsonTokenSafetyCandidateEvidenceReportStore:
    def __init__(self, file_path: str | os.PathLike[str]) -> None:
        self._file_path = Path(file_path)
        self._report: TokenSafetyCandidateEvidenceReport | None = None
        self._load()

    def save(self, report: TokenSafetyCandidateEvidenceReport) -> str:
        if not isinstance(report, TokenSafetyCandidateEvidenceReport):
            raise TypeError("report must be TokenSafetyCandidateEvidenceReport")
        if self._report is not None and self._report != report:
            raise RuntimeError("token safety report identity collision")
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        document = {"report": report.canonical_dict(), "schema_version": _SCHEMA_VERSION}
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(document))
            stream.flush()
            os.fsync(stream.fileno())
        atomic_replace(temporary, self._file_path)
        self._report = report
        return report.report_id

    def load(self) -> TokenSafetyCandidateEvidenceReport | None:
        return self._report

    def _load(self) -> None:
        if not self._file_path.is_file():
            return
        try:
            raw = self._file_path.read_text(encoding="utf-8")
            document: Any = json.loads(raw)
            if document["schema_version"] != _SCHEMA_VERSION:
                raise ValueError("unsupported report store schema_version")
            row = document["report"]["row"]
            candidate = row["candidate"]
            binding = row["binding"]
            candidate_obj = SolanaWalletTokenCandidate(
                wallet=candidate["wallet"], mint=candidate["mint"],
                activity_count=candidate["activity_count"], buy_count=candidate["buy_count"],
                first_slot=candidate["first_slot"], last_slot=candidate["last_slot"],
                reasons=tuple(candidate["reasons"]), candidate_id=candidate["candidate_id"],
                schema_version=candidate["schema_version"],
            )
            binding_obj = TokenSafetyCandidateBinding(
                candidate_id=binding["candidate_id"], token_observation_id=binding["token_observation_id"],
                wallet=binding["wallet"], token=binding["token"],
                liquidity_amount=binding["liquidity_amount"],
                holder_concentration_bps=binding["holder_concentration_bps"],
                mint_authority=binding["mint_authority"], freeze_authority=binding["freeze_authority"],
                update_authority=binding["update_authority"], binding_id=binding["binding_id"],
                schema_version=binding["schema_version"],
            )
            report_row = TokenSafetyCandidateReadRow(
                candidate=candidate_obj, binding=binding_obj,
                binding_evidence_id=row["binding_evidence_id"],
                replay_verified=row["replay_verified"],
            )
            self._report = TokenSafetyCandidateEvidenceReport(
                row=report_row,
                report_id=document["report"]["report_id"],
                schema_version=document["report"]["schema_version"],
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid token safety report store") from exc
        if canonical_json(document) != raw:
            raise ValueError("token safety report store is not canonical JSON")


__all__ = ["JsonTokenSafetyCandidateEvidenceReportStore"]
