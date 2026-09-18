from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from smart_money.adapters.solana_signature_ingestion import (
    bind_normalized_signature,
)
from smart_money.adapters.solana_signature_normalizer import (
    SolanaSignatureNormalizer,
    TradeDirection,
)
from smart_money.application.ports.evidence_ledger import EvidenceLedger
from smart_money.domain.solana_program_registry import SOLANA_DEX_SCAN_PROGRAMS

DEX_PROGRAMS = SOLANA_DEX_SCAN_PROGRAMS

_WALLET_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
_SIGNATURE_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{64,100}$")


class SolanaDexRPC(Protocol):
    def capture_signatures(
        self, address: str, limit: int = 20, before: str | None = None
    ) -> Mapping[str, Any]: ...

    def capture_transaction(self, signature: str) -> Mapping[str, Any]: ...


@dataclass(frozen=True, slots=True)
class DexFetchOptions:
    dex: str = "raydium_amm"
    limit: int = 10
    scan_limit: int = 100
    wallet: str | None = None

    def __post_init__(self) -> None:
        if self.dex not in DEX_PROGRAMS:
            raise ValueError("unsupported DEX")
        if not 1 <= self.limit <= 1000:
            raise ValueError("limit must be 1..1000")
        if not self.limit <= self.scan_limit <= 100_000:
            raise ValueError("scan_limit must be between limit and 100000")
        if self.wallet is not None and _WALLET_PATTERN.fullmatch(self.wallet) is None:
            raise ValueError("wallet must be a Solana Base58 public key")


@dataclass(frozen=True, slots=True)
class DexSwapRecord:
    signature: str
    dex: str
    slot: int
    block_time: int | None
    direction: str
    wallet: str
    observation_id: str
    evidence_id: str | None

    def canonical_dict(self) -> dict[str, object]:
        return {
            "block_time": self.block_time,
            "dex": self.dex,
            "direction": self.direction,
            "evidence_id": self.evidence_id,
            "observation_id": self.observation_id,
            "signature": self.signature,
            "slot": self.slot,
            "wallet": self.wallet,
        }


@dataclass(frozen=True, slots=True)
class DexFetchReport:
    records: tuple[DexSwapRecord, ...]
    scanned_signatures: int
    rejected_failed: int
    rejected_non_signer: int
    rejected_unknown: int
    rejected_rpc: int
    exhausted: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "exhausted": self.exhausted,
            "records": tuple(item.canonical_dict() for item in self.records),
            "rejected_failed": self.rejected_failed,
            "rejected_non_signer": self.rejected_non_signer,
            "rejected_rpc": self.rejected_rpc,
            "rejected_unknown": self.rejected_unknown,
            "scanned_signatures": self.scanned_signatures,
            "schema_version": "solana_dex_fetch_report.v1",
        }


def _result(response: Mapping[str, Any]) -> Mapping[str, Any] | None:
    value = response.get("result")
    return value if isinstance(value, Mapping) else None


def fetch_dex_swaps(
    rpc: SolanaDexRPC,
    options: DexFetchOptions,
    *,
    ledger: EvidenceLedger | None = None,
) -> DexFetchReport:
    records: list[DexSwapRecord] = []
    before: str | None = None
    scanned = failed = non_signer = unknown = rpc_rejected = 0
    exhausted = False
    program = DEX_PROGRAMS[options.dex]
    while len(records) < options.limit and scanned < options.scan_limit:
        page_limit = min(100, options.scan_limit - scanned)
        response = rpc.capture_signatures(program, page_limit, before)
        rows = response.get("result")
        if not isinstance(rows, list):
            raise TypeError("signature response result must be a list")
        if not rows:
            exhausted = True
            break
        for row in rows:
            if len(records) >= options.limit:
                break
            if not isinstance(row, Mapping):
                raise TypeError("signature row must be a mapping")
            signature = row.get("signature")
            if not isinstance(signature, str) or _SIGNATURE_PATTERN.fullmatch(signature) is None:
                raise ValueError("signature cursor is invalid")
            scanned += 1
            try:
                transaction_response = rpc.capture_transaction(signature)
            except (OSError, RuntimeError):
                rpc_rejected += 1
                continue
            transaction = _result(transaction_response)
            if transaction is None:
                failed += 1
                continue
            meta = transaction.get("meta")
            if not isinstance(meta, Mapping) or meta.get("err") is not None:
                failed += 1
                continue
            try:
                normalized = SolanaSignatureNormalizer.normalize(transaction_response)
            except (TypeError, ValueError):
                failed += 1
                continue
            if options.wallet is not None and normalized.raw.signer != options.wallet:
                non_signer += 1
                continue
            if normalized.classification.direction is TradeDirection.UNKNOWN:
                unknown += 1
                continue
            evidence_id = None
            if ledger is not None:
                evidence_id = bind_normalized_signature(
                    ledger, transaction_response
                ).evidence_id
            records.append(
                DexSwapRecord(
                    signature=normalized.raw.signature,
                    dex=options.dex,
                    slot=normalized.raw.slot,
                    block_time=normalized.raw.block_time,
                    direction=normalized.classification.direction.value,
                    wallet=normalized.raw.signer,
                    observation_id=normalized.observation.observation_id,
                    evidence_id=evidence_id,
                )
            )
        last = rows[-1]
        cursor = last.get("signature") if isinstance(last, Mapping) else None
        if not isinstance(cursor, str) or _SIGNATURE_PATTERN.fullmatch(cursor) is None:
            raise ValueError("signature pagination cursor is invalid")
        if cursor == before:
            raise ValueError("signature pagination cursor did not advance")
        before = cursor
        if len(rows) < page_limit:
            exhausted = True
            break
    return DexFetchReport(
        tuple(records), scanned, failed, non_signer, unknown, rpc_rejected, exhausted
    )


__all__ = [
    "DEX_PROGRAMS",
    "DexFetchOptions",
    "DexFetchReport",
    "DexSwapRecord",
    "SolanaDexRPC",
    "fetch_dex_swaps",
]
