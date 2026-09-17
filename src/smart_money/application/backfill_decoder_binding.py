from __future__ import annotations

from typing import Any, Mapping

from smart_money.application.solana_decoder import build_transaction_envelope, project_decoder_evidence
from smart_money.application.ports.evidence_ledger import EvidenceLedger


def _canonicalize_rpc(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".15g")
    if isinstance(value, Mapping):
        return {str(key): _canonicalize_rpc(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_canonicalize_rpc(item) for item in value]
    return value


def decode_and_bind_transaction(ledger: EvidenceLedger, response: Mapping[str, Any]) -> str:
    result = response.get("result", response)
    if not isinstance(result, Mapping):
        raise ValueError("transaction response result must be a mapping")
    result = _canonicalize_rpc(result)
    transaction = result.get("transaction", {})
    message = transaction.get("message", {}) if isinstance(transaction, Mapping) else {}
    envelope = build_transaction_envelope(str(result.get("signature", "backfill")), int(result.get("slot", 0)), message, result.get("blockTime"))
    payload = project_decoder_evidence(envelope)
    return ledger.append(payload)


__all__ = ["decode_and_bind_transaction"]
