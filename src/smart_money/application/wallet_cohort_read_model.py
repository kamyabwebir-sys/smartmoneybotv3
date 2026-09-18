from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.wallet_behavior_fingerprint import WalletBehaviorFingerprint
from smart_money.application.wallet_cohort_audit import WalletCohortAuditReceipt
from smart_money.application.wallet_cohort_detection import WalletCohort
from smart_money.application.wallet_cohort_replay import WalletCohortReplayReceipt
from smart_money.core.ids import deterministic_id

_SCHEMA_VERSION = "wallet_cohort_read_model.v1"


@dataclass(frozen=True, slots=True)
class WalletCohortReadRow:
    cohort: WalletCohort
    fingerprints: tuple[WalletBehaviorFingerprint, ...]
    replay_receipt: WalletCohortReplayReceipt
    audit_receipt: WalletCohortAuditReceipt

    def __post_init__(self) -> None:
        if not isinstance(self.cohort, WalletCohort):
            raise TypeError("cohort must be WalletCohort")
        if not isinstance(self.fingerprints, tuple) or not all(
            isinstance(item, WalletBehaviorFingerprint) for item in self.fingerprints
        ):
            raise TypeError("fingerprints must be a tuple of WalletBehaviorFingerprint")
        if tuple(item.fingerprint_id for item in self.fingerprints) != self.cohort.fingerprint_ids:
            raise ValueError("fingerprints do not match cohort")
        if not isinstance(self.replay_receipt, WalletCohortReplayReceipt):
            raise TypeError("replay_receipt must be WalletCohortReplayReceipt")
        if not isinstance(self.audit_receipt, WalletCohortAuditReceipt):
            raise TypeError("audit_receipt must be WalletCohortAuditReceipt")
        if self.replay_receipt.cohort_id != self.cohort.cohort_id:
            raise ValueError("replay receipt cohort mismatch")
        if self.audit_receipt.cohort_id != self.cohort.cohort_id:
            raise ValueError("audit receipt cohort mismatch")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "audit_receipt": self.audit_receipt.canonical_dict(),
            "cohort": self.cohort.canonical_dict(),
            "fingerprints": tuple(item.canonical_dict() for item in self.fingerprints),
            "replay_receipt": self.replay_receipt.canonical_dict(),
        }


@dataclass(frozen=True, slots=True)
class WalletCohortReadModel:
    rows: tuple[WalletCohortReadRow, ...]
    model_id: str
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.rows, tuple) or not all(
            isinstance(item, WalletCohortReadRow) for item in self.rows
        ):
            raise TypeError("rows must be a tuple of WalletCohortReadRow")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported wallet cohort read model schema_version")
        expected = deterministic_id(
            "wallet_cohort_read_model",
            {"rows": tuple(item.canonical_dict() for item in self.rows), "schema_version": self.schema_version},
        )
        if self.model_id != expected:
            raise ValueError("model_id does not match rows")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "rows": tuple(item.canonical_dict() for item in self.rows),
            "schema_version": self.schema_version,
        }


def build_wallet_cohort_read_model(
    cohorts: tuple[WalletCohort, ...],
    fingerprints: tuple[WalletBehaviorFingerprint, ...],
    replay_receipts: tuple[WalletCohortReplayReceipt, ...],
    audit_receipts: tuple[WalletCohortAuditReceipt, ...],
) -> WalletCohortReadModel:
    if not all(isinstance(value, tuple) for value in (cohorts, fingerprints, replay_receipts, audit_receipts)):
        raise TypeError("read model inputs must be tuples")
    fingerprint_map = {item.fingerprint_id: item for item in fingerprints}
    replay_map = {item.cohort_id: item for item in replay_receipts}
    audit_map = {item.cohort_id: item for item in audit_receipts}
    rows: list[WalletCohortReadRow] = []
    for cohort in cohorts:
        if not isinstance(cohort, WalletCohort):
            raise TypeError("cohorts must contain WalletCohort")
        members = tuple(fingerprint_map[item] for item in cohort.fingerprint_ids if item in fingerprint_map)
        if len(members) != len(cohort.fingerprint_ids):
            raise ValueError("cohort fingerprint evidence is incomplete")
        if cohort.cohort_id not in replay_map or cohort.cohort_id not in audit_map:
            raise ValueError("cohort replay or audit receipt is missing")
        rows.append(WalletCohortReadRow(cohort, members, replay_map[cohort.cohort_id], audit_map[cohort.cohort_id]))
    rows.sort(key=lambda item: item.cohort.cohort_id)
    identity = {"rows": tuple(item.canonical_dict() for item in rows), "schema_version": _SCHEMA_VERSION}
    return WalletCohortReadModel(tuple(rows), deterministic_id("wallet_cohort_read_model", identity))


__all__ = ["WalletCohortReadModel", "WalletCohortReadRow", "build_wallet_cohort_read_model"]
