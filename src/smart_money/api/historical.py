from __future__ import annotations

from typing import Any

from smart_money.application.solana_dex_attribution import (
    build_historical_api_response,
    build_historical_query_audit,
    query_historical_candidates,
    verify_historical_query_replay,
)


def require_read_only(token: str | None, expected: str | None) -> None:
    if expected is not None and token != expected:
        raise PermissionError("read-only authentication failed")


def historical_overview(model: dict[str, Any], *, token: str | None = None, expected_token: str | None = None) -> dict[str, Any]:
    require_read_only(token, expected_token)
    return build_historical_api_response(model)


def historical_candidates(model: dict[str, Any], *, page: int = 1, page_size: int = 50, token: str | None = None, expected_token: str | None = None) -> dict[str, Any]:
    require_read_only(token, expected_token)
    return query_historical_candidates(model, page=page, page_size=page_size)


def historical_audit(model: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    return build_historical_query_audit(model, parameters)


def historical_replay(expected: dict[str, Any], replayed: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": "historical_replay_verification.v1", "matching": verify_historical_query_replay(expected, replayed)}


__all__ = ["require_read_only", "historical_overview", "historical_candidates", "historical_audit", "historical_replay"]
