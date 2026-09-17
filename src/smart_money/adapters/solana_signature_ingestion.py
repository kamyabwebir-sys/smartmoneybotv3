from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from smart_money.adapters.solana_signature_normalizer import (
    SolanaSignatureNormalizer,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.application.solana_observation_parser import SolanaObservationParser


@dataclass(frozen=True, slots=True)
class NormalizedSignatureIngestionReceipt:
    signature: str
    observation_id: str
    evidence_id: str
    direction: str
    wallet: str
    slot: int
    duplicate: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "direction": self.direction,
            "duplicate": self.duplicate,
            "evidence_id": self.evidence_id,
            "observation_id": self.observation_id,
            "signature": self.signature,
            "slot": self.slot,
            "wallet": self.wallet,
        }


def bind_normalized_signature(
    ledger: EvidenceLedger,
    payload: Mapping[str, Any],
    *,
    observed_at: int | None = None,
) -> NormalizedSignatureIngestionReceipt:
    if not isinstance(ledger, EvidenceLedger):
        raise TypeError("ledger must satisfy EvidenceLedger")
    normalized = SolanaSignatureNormalizer.normalize(
        payload,
        observed_at=observed_at,
    )
    evidence = SolanaObservationParser.from_observation(normalized.observation).payload
    evidence_id = evidence.get_canonical_id()
    duplicate = ledger.contains(evidence_id)
    persisted_id = ledger.append(evidence)
    if persisted_id != evidence_id:
        raise ValueError("ledger returned a non-canonical evidence identity")
    return NormalizedSignatureIngestionReceipt(
        signature=normalized.raw.signature,
        observation_id=normalized.observation.observation_id,
        evidence_id=evidence_id,
        direction=normalized.classification.direction.value,
        wallet=normalized.raw.signer,
        slot=normalized.raw.slot,
        duplicate=duplicate,
    )


def bind_normalized_signature_batch(
    ledger: EvidenceLedger,
    payloads: Iterable[Mapping[str, Any]],
) -> tuple[NormalizedSignatureIngestionReceipt, ...]:
    receipts = tuple(bind_normalized_signature(ledger, payload) for payload in payloads)
    return tuple(sorted(receipts, key=lambda item: (item.slot, item.signature)))


__all__ = [
    "NormalizedSignatureIngestionReceipt",
    "bind_normalized_signature",
    "bind_normalized_signature_batch",
]
