from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from smart_money.application.ports.recovery_gated_run_store import (
    RecoveryGatedRunStore,
)
from smart_money.application.recovery_gated_ingestion import (
    RecoveryGatedIngestionResult,
)
from smart_money.core.ids import deterministic_id
from smart_money.domain.market_identity import MarketId

_SCHEMA_VERSION = "durable_recovery_gated_ingestion.v1"
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


def _require_sha256(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")
    return value


def _require_result_count(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


@runtime_checkable
class RecoveryGatedIngestionRunner(Protocol):
    async def run(
        self,
        market: MarketId,
        *,
        max_events: int | None = None,
        advance_if_required: bool = False,
    ) -> RecoveryGatedIngestionResult:
        """Run one recovery-gated ingestion session."""
        ...


@dataclass(frozen=True, slots=True)
class DurableRecoveryGatedIngestionReceipt:
    """Proof that a recovery-gated result was retained by its durable store."""

    receipt_id: str
    result: RecoveryGatedIngestionResult
    run_store_content_hash: str
    run_store_result_count: int
    newly_persisted: bool
    schema_version: str = _SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.receipt_id, str) or not self.receipt_id.strip():
            raise ValueError("receipt_id must be a non-empty string")
        object.__setattr__(self, "receipt_id", self.receipt_id.strip())
        if not isinstance(self.result, RecoveryGatedIngestionResult):
            raise TypeError("result must be a RecoveryGatedIngestionResult")
        object.__setattr__(
            self,
            "run_store_content_hash",
            _require_sha256(
                self.run_store_content_hash,
                "run_store_content_hash",
            ),
        )
        _require_result_count(
            self.run_store_result_count,
            "run_store_result_count",
        )
        if self.run_store_result_count == 0:
            raise ValueError("run_store_result_count must be positive")
        if not isinstance(self.newly_persisted, bool):
            raise TypeError("newly_persisted must be a boolean")
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(
                "unsupported durable recovery-gated ingestion schema_version"
            )
        expected_id = deterministic_id(
            "durable_recovery_gated_ingestion",
            self.identity_payload(),
        )
        if self.receipt_id != expected_id:
            raise ValueError("receipt_id does not match deterministic payload")

    def identity_payload(self) -> dict[str, object]:
        return {
            "newly_persisted": self.newly_persisted,
            "result": self.result.canonical_dict(),
            "run_store_content_hash": self.run_store_content_hash,
            "run_store_result_count": self.run_store_result_count,
            "schema_version": self.schema_version,
        }

    def canonical_dict(self) -> dict[str, object]:
        return {"receipt_id": self.receipt_id, **self.identity_payload()}

    @property
    def run_id(self) -> str:
        return self.result.run_id

    @property
    def gate_decision_id(self) -> str:
        return self.result.gate_decision_id

    @property
    def ingestion_session_id(self) -> str:
        return self.result.ingestion_session_id


@dataclass(frozen=True, slots=True)
class DurableRecoveryGatedIngestionOrchestrator:
    """Run gated ingestion and prove exact durable result retention."""

    runner: RecoveryGatedIngestionRunner
    result_store: RecoveryGatedRunStore

    def __post_init__(self) -> None:
        if not isinstance(self.runner, RecoveryGatedIngestionRunner):
            raise TypeError(
                "runner must satisfy RecoveryGatedIngestionRunner"
            )
        if not isinstance(self.result_store, RecoveryGatedRunStore):
            raise TypeError("result_store must satisfy RecoveryGatedRunStore")

    async def run(
        self,
        market: MarketId,
        *,
        max_events: int | None = None,
        advance_if_required: bool = False,
    ) -> DurableRecoveryGatedIngestionReceipt:
        self._validate_request(
            market=market,
            max_events=max_events,
            advance_if_required=advance_if_required,
        )
        result = await self.runner.run(
            market,
            max_events=max_events,
            advance_if_required=advance_if_required,
        )
        if not isinstance(result, RecoveryGatedIngestionResult):
            raise RuntimeError(
                "recovery-gated runner returned an invalid result type"
            )
        if result.ingestion_result.market_id != market.canonical_id:
            raise RuntimeError(
                "recovery-gated result market does not match requested market"
            )

        before_count = _require_result_count(
            self.result_store.result_count,
            "result_store.result_count",
        )
        before_hash = _require_sha256(
            self.result_store.content_hash,
            "result_store.content_hash",
        )
        existing = self.result_store.get(result.run_id)
        self._require_stable_snapshot(before_count, before_hash)
        if existing is not None and existing != result:
            raise RuntimeError("recovery-gated run identity collision")
        newly_persisted = existing is None

        recorded_id = self.result_store.append(result)
        if recorded_id != result.run_id:
            raise RuntimeError(
                "result store acknowledgement does not match run_id"
            )
        retained = self.result_store.get(result.run_id)
        if retained != result:
            raise RuntimeError(
                "result store did not retain the exact ingestion result"
            )

        expected_count = before_count + (1 if newly_persisted else 0)
        after_count = _require_result_count(
            self.result_store.result_count,
            "result_store.result_count",
        )
        after_hash = _require_sha256(
            self.result_store.content_hash,
            "result_store.content_hash",
        )
        if after_count != expected_count:
            raise RuntimeError("result store count changed unexpectedly")
        if not newly_persisted and after_hash != before_hash:
            raise RuntimeError(
                "duplicate append changed result store content hash"
            )
        self._require_stable_snapshot(after_count, after_hash)

        payload: dict[str, object] = {
            "newly_persisted": newly_persisted,
            "result": result.canonical_dict(),
            "run_store_content_hash": after_hash,
            "run_store_result_count": after_count,
            "schema_version": _SCHEMA_VERSION,
        }
        return DurableRecoveryGatedIngestionReceipt(
            receipt_id=deterministic_id(
                "durable_recovery_gated_ingestion",
                payload,
            ),
            result=result,
            run_store_content_hash=after_hash,
            run_store_result_count=after_count,
            newly_persisted=newly_persisted,
        )

    def _require_stable_snapshot(
        self,
        expected_count: int,
        expected_hash: str,
    ) -> None:
        if self.result_store.result_count != expected_count:
            raise RuntimeError("result store changed during verification")
        if self.result_store.content_hash != expected_hash:
            raise RuntimeError("result store changed during verification")

    @staticmethod
    def _validate_request(
        *,
        market: MarketId,
        max_events: int | None,
        advance_if_required: bool,
    ) -> None:
        if not isinstance(market, MarketId):
            raise TypeError("market must be a MarketId")
        if max_events is not None:
            if isinstance(max_events, bool) or not isinstance(max_events, int):
                raise TypeError("max_events must be an integer or None")
            if max_events <= 0:
                raise ValueError("max_events must be positive")
        if not isinstance(advance_if_required, bool):
            raise TypeError("advance_if_required must be a boolean")


__all__ = [
    "DurableRecoveryGatedIngestionOrchestrator",
    "DurableRecoveryGatedIngestionReceipt",
    "RecoveryGatedIngestionRunner",
]
