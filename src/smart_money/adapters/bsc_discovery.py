from __future__ import annotations

import json
from typing import Any, Callable, Mapping
from urllib.request import Request, urlopen


class BSCDiscoveryAdapter:
    def __init__(self, rpc_url: str, opener: Callable[..., Any] = urlopen) -> None:
        if not rpc_url.startswith(("https://", "http://")):
            raise ValueError("BSC RPC URL must be HTTP(S)")
        self.rpc_url = rpc_url
        self._opener = opener

    def request(self, method: str, params: list[Any] | None = None) -> Mapping[str, Any]:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}).encode()
        with self._opener(Request(self.rpc_url, data=body, headers={"content-type": "application/json"}, method="POST"), timeout=10) as response:
            payload = json.loads(response.read().decode())
        if not isinstance(payload, Mapping) or payload.get("error") is not None:
            raise RuntimeError("BSC RPC request failed")
        return payload


def decode_bsc_activity(transfers: tuple[Mapping[str, Any], ...], wallet: str) -> tuple[dict[str, Any], ...]:
    if not wallet.startswith("0x") or len(wallet) != 42:
        raise ValueError("invalid BSC wallet")
    result = []
    for item in transfers:
        direction = "BUY" if str(item.get("to", "")).lower() == wallet.lower() else "SELL"
        result.append({"wallet": wallet.lower(), "token": item.get("token"), "value": item.get("value", "0"), "direction": direction})
    return tuple(result)


def rank_bsc_candidates(activities: tuple[Mapping[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    counts: dict[str, int] = {}
    for activity in activities:
        wallet = str(activity.get("wallet", "")).lower()
        if wallet:
            counts[wallet] = counts.get(wallet, 0) + 1
    return tuple({"wallet": wallet, "activity_count": count, "chain": "bsc"} for wallet, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])))


__all__ = ["BSCDiscoveryAdapter", "decode_bsc_activity", "rank_bsc_candidates"]
