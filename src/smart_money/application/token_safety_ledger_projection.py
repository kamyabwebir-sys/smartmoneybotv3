from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.core.ids import deterministic_id
from smart_money.domain.token_safety import TokenSafetyObservation
from smart_money.ingestion.contracts import EvidencePayload

_SCHEMA_VERSION = "token_safety_ledger_projection.v1"


@dataclass(frozen=True, slots=True)
class TokenSafetyLedgerReceipt:
    receipt_id: str
    observation_id: str
    evidence_id: str
    ledger_entry_count: int
    already_present: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("receipt_id", "observation_id", "evidence_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if isinstance(self.ledger_entry_count, bool) or not isinstance(
            self.ledger_entry_count, int
        ) or self.ledger_entry_count < 0:
            raise ValueError("ledger_entry_count must be a non-negative integer")
        if not isinstance(self.already_present, bool):
            raise TypeError("already_present must be boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError("unsupported token safety ledger schema_version")
        if self.receipt_id != deterministic_id(
            "token_safety_ledger", self.identity_payload()
        ):
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, Any]:
        return {
            "already_present": self.already_present,
            "evidence_id": self.evidence_id,
            "ledger_entry_count": self.ledger_entry_count,
            "observation_id": self.observation_id,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}


def ingest_token_safety_observation(
    observation: TokenSafetyObservation, ledger: EvidenceLedger
) -> TokenSafetyLedgerReceipt:
    if not isinstance(observation, TokenSafetyObservation):
        raise TypeError("observation must be TokenSafetyObservation")
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    payload = EvidencePayload(
        source_id="token_safety",
        evidence_type="token_safety_observation",
        timestamp=observation.observed_at,
        data={"token_safety": observation.canonical_dict()},
        metadata={
            "authority": "NONE",
            "classification": "EVIDENCE",
            "verification_status": "PROVISIONAL",
            "provenance": {
                "observation_id": observation.observation_id,
                "source_id": "token_safety",
                "source_schema_version": observation.schema_version,
            },
        },
    )
    evidence_id = payload.get_canonical_id()
    already_present = ledger.contains(evidence_id)
    before_count = ledger.entry_count
    if ledger.append(payload) != evidence_id or ledger.get(evidence_id) != payload:
        raise ValueError("Ledger retained token safety payload mismatch")
    expected_count = before_count if already_present else before_count + 1
    if ledger.entry_count != expected_count:
        raise ValueError("Ledger entry count violates idempotent append contract")
    identity = {
        "already_present": already_present,
        "evidence_id": evidence_id,
        "ledger_entry_count": ledger.entry_count,
        "observation_id": observation.observation_id,
        "schema_version": _SCHEMA_VERSION,
    }
    return TokenSafetyLedgerReceipt(
        receipt_id=deterministic_id("token_safety_ledger", identity),
        observation_id=observation.observation_id,
        evidence_id=evidence_id,
        ledger_entry_count=ledger.entry_count,
        already_present=already_present,
    )


__all__ = ["TokenSafetyLedgerReceipt", "ingest_token_safety_observation"]
