from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from smart_money.application.production_shadow import SolanaRPCConfig


class SolanaRPCFetcher:
    def __init__(self, config: SolanaRPCConfig, opener: Callable[..., Any] = urlopen) -> None:
        self.config = config
        self._opener = opener
        self.request_count = 0
        self.retry_count = 0

    def request(self, method: str, params: list[Any] | None = None) -> Mapping[str, Any]:
        self.request_count += 1
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}).encode()
        request = Request(self.config.url, data=body, headers={"content-type": "application/json"}, method="POST")
        with self._opener(request, timeout=self.config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, Mapping):
            raise RuntimeError("Solana RPC returned a non-object response")  # noqa: TRY004 - provider failure contract
        if "error" in payload and payload["error"] is not None:
            error = payload["error"]
            code = error.get("code") if isinstance(error, Mapping) else "unknown"
            code = code if type(code) is int else "unknown"
            raise RuntimeError(f"Solana RPC error code: {code}")
        return payload

    def capture_signatures(self, address: str, limit: int = 20, before: str | None = None) -> Mapping[str, Any]:
        if not address.strip() or limit < 1 or limit > 1000:
            raise ValueError("invalid address or limit")
        options: dict[str, Any] = {"limit": limit}
        if before:
            options["before"] = before.strip()
        return self.request_with_retry("getSignaturesForAddress", [address.strip(), options])

    def capture_transaction(self, signature: str) -> Mapping[str, Any]:
        if not signature.strip():
            raise ValueError("signature must be non-empty")
        return self.request_with_retry("getTransaction", [signature.strip(), {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}])

    def capture_token_safety(self, mint: str) -> Mapping[str, Any]:
        if not isinstance(mint, str) or not mint.strip():
            raise ValueError("mint must be non-empty")
        mint = mint.strip()
        return {
            "mint_account": self.request_with_retry("getAccountInfo", [mint, {"encoding": "jsonParsed"}]),
            "largest_accounts": self.request_with_retry("getTokenLargestAccounts", [mint]),
        }

    def request_with_retry(self, method: str, params: list[Any] | None = None, *, max_retries: int = 3, base_delay: float = 0.1) -> Mapping[str, Any]:
        if type(max_retries) is not int or not 0 <= max_retries <= 5 or not 0 <= base_delay <= 10:
            raise ValueError("retry settings exceed bounded policy")
        for attempt in range(max_retries + 1):
            try:
                return self.request(method, params)
            except OSError as exc:
                if isinstance(exc, HTTPError) and exc.code not in {408, 429, 500, 502, 503, 504}:
                    raise OSError("permanent RPC HTTP failure") from None
                if attempt >= max_retries:
                    raise OSError("RPC transport retries exhausted") from None
                self.retry_count += 1
                time.sleep(min(10, base_delay * (2**attempt)))


__all__ = ["SolanaRPCFetcher"]
