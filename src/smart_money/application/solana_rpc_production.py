from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from smart_money.core.ids import deterministic_id
from pathlib import Path
import json


class SolanaRPCTransport:
    def request(self, method: str, params: tuple[Any, ...]) -> Mapping[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class CallableRPCTransport:
    handler: Callable[[str, tuple[Any, ...]], Mapping[str, Any]]

    def request(self, method: str, params: tuple[Any, ...]) -> Mapping[str, Any]:
        if not callable(self.handler):
            raise TypeError("handler must be callable")
        return self.handler(method, params)


def classify_rpc_error(error: Mapping[str, Any]) -> str:
    if not isinstance(error, Mapping):
        raise TypeError("error must be mapping")
    code = error.get("code")
    if code in {-32005, 429}:
        return "RATE_LIMIT"
    if code in {-32601, -32602}:
        return "REQUEST_INVALID"
    return "UPSTREAM_ERROR"


@dataclass(frozen=True, slots=True)
class RetryExecutionEvidence:
    provider_id: str
    retry_count: int
    error_class: str
    evidence_id: str
    schema_version: str = "retry_execution_evidence.v1"

    def __post_init__(self) -> None:
        if (
            self.retry_count < 0
            or not self.provider_id.strip()
            or not self.error_class.strip()
        ):
            raise ValueError("invalid retry evidence")
        expected = deterministic_id(
            "retry_execution_evidence",
            {
                "error_class": self.error_class,
                "provider_id": self.provider_id.strip(),
                "retry_count": self.retry_count,
                "schema_version": self.schema_version,
            },
        )
        if self.evidence_id != expected:
            raise ValueError("evidence_id mismatch")


def build_retry_execution_evidence(
    provider_id: str, *, retry_count: int, error_class: str
) -> RetryExecutionEvidence:
    identity = {
        "error_class": error_class.strip(),
        "provider_id": provider_id.strip(),
        "retry_count": retry_count,
        "schema_version": "retry_execution_evidence.v1",
    }
    return RetryExecutionEvidence(
        provider_id,
        retry_count,
        error_class,
        deterministic_id("retry_execution_evidence", identity),
    )


class PersistentCursorRunner:
    def __init__(self, path: str | Path, cursor: int = 0) -> None:
        if cursor < 0:
            raise ValueError("cursor must be non-negative")
        self.path = Path(path)
        self.cursor = cursor

    def run_once(self, fetch: Callable[[int], Mapping[str, Any]]) -> Mapping[str, Any]:
        result = fetch(self.cursor)
        if not isinstance(result, Mapping):
            raise TypeError("result must be mapping")
        self.cursor = int(result.get("slot", self.cursor))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"cursor": self.cursor}, sort_keys=True), encoding="utf-8"
        )
        return result


@dataclass(frozen=True, slots=True)
class LiveTransactionFetch:
    signature: str
    slot: int
    response: Mapping[str, Any]
    fetch_id: str
    schema_version: str = "live_transaction_fetch.v1"

    def __post_init__(self) -> None:
        if not self.signature.strip() or self.slot < 0:
            raise ValueError("invalid transaction fetch")
        if self.fetch_id != deterministic_id(
            "live_transaction_fetch",
            {
                "response": dict(self.response),
                "schema_version": self.schema_version,
                "signature": self.signature.strip(),
                "slot": self.slot,
            },
        ):
            raise ValueError("fetch_id mismatch")


def fetch_live_transaction(
    signature: str, slot: int, response: Mapping[str, Any]
) -> LiveTransactionFetch:
    identity = {
        "response": dict(response),
        "schema_version": "live_transaction_fetch.v1",
        "signature": signature.strip(),
        "slot": slot,
    }
    return LiveTransactionFetch(
        signature, slot, response, deterministic_id("live_transaction_fetch", identity)
    )


def normalize_rpc_response(response: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(response, Mapping) or "result" not in response:
        raise ValueError("RPC response must contain result")
    if "error" in response and response["error"] is not None:
        raise ValueError("RPC response contains error")
    return {
        "result": response["result"],
        "id": response.get("id", 1),
        "jsonrpc": response.get("jsonrpc", "2.0"),
    }


@dataclass(frozen=True, slots=True)
class RateLimitBackoff:
    max_retries: int
    base_slots: int

    def __post_init__(self) -> None:
        if self.max_retries < 0 or self.base_slots < 0:
            raise ValueError("backoff values must be non-negative")

    def delay_slots(self, retry: int) -> int:
        if retry < 0:
            raise ValueError("retry must be non-negative")
        return self.base_slots * (2**retry)


def run_cursor_loop(
    fetch: Callable[[int], Mapping[str, Any]], start_slot: int, *, steps: int = 1
) -> tuple[Mapping[str, Any], ...]:
    if start_slot < 0 or steps < 0:
        raise ValueError("cursor values must be non-negative")
    results = []
    cursor = start_slot
    for _ in range(steps):
        result = fetch(cursor)
        if not isinstance(result, Mapping):
            raise TypeError("fetch result must be mapping")
        results.append(result)
        cursor = int(result.get("slot", cursor))
    return tuple(results)


@dataclass(frozen=True, slots=True)
class ProductionReplayFixture:
    requests: tuple[Mapping[str, Any], ...]
    responses: tuple[Mapping[str, Any], ...]
    fixture_id: str
    schema_version: str = "solana_production_replay_fixture.v1"

    def __post_init__(self) -> None:
        if len(self.requests) != len(self.responses):
            raise ValueError("requests and responses must have equal length")
        expected = deterministic_id(
            "solana_production_replay_fixture",
            {
                "requests": tuple(dict(x) for x in self.requests),
                "responses": tuple(dict(x) for x in self.responses),
                "schema_version": self.schema_version,
            },
        )
        if self.fixture_id != expected:
            raise ValueError("fixture_id mismatch")


@dataclass(frozen=True, slots=True)
class ProductionConnectorHealthEvidence:
    provider_id: str
    request_count: int
    failure_count: int
    evidence_id: str
    schema_version: str = "production_connector_health.v1"

    def __post_init__(self) -> None:
        if (
            not self.provider_id.strip()
            or self.request_count < 0
            or not 0 <= self.failure_count <= self.request_count
        ):
            raise ValueError("invalid health evidence")
        expected = deterministic_id(
            "production_connector_health",
            {
                "failure_count": self.failure_count,
                "provider_id": self.provider_id.strip(),
                "request_count": self.request_count,
                "schema_version": self.schema_version,
            },
        )
        if self.evidence_id != expected:
            raise ValueError("evidence_id mismatch")


def build_connector_health(
    provider_id: str, *, request_count: int, failure_count: int
) -> ProductionConnectorHealthEvidence:
    identity = {
        "failure_count": failure_count,
        "provider_id": provider_id.strip(),
        "request_count": request_count,
        "schema_version": "production_connector_health.v1",
    }
    return ProductionConnectorHealthEvidence(
        provider_id,
        request_count,
        failure_count,
        deterministic_id("production_connector_health", identity),
    )


__all__ = [
    "SolanaRPCTransport",
    "normalize_rpc_response",
    "RateLimitBackoff",
    "run_cursor_loop",
    "ProductionReplayFixture",
    "ProductionConnectorHealthEvidence",
    "build_connector_health",
]
