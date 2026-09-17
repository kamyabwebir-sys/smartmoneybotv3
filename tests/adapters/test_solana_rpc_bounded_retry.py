from urllib.error import HTTPError

import pytest

from smart_money.adapters.solana_rpc_fetcher import SolanaRPCFetcher
from smart_money.application.production_shadow import SolanaRPCConfig


@pytest.mark.parametrize("failure,attempts", [(TimeoutError("secret-url"), 4),
                                             (HTTPError("secret-url", 429, "limited", {}, None), 4),
                                             (HTTPError("secret-url", 401, "denied", {}, None), 1)])
def test_transport_retry_bounded_and_redacted(monkeypatch, failure, attempts):
    calls, delays = [], []

    def opener(*args, **kwargs):
        calls.append(1)
        raise failure

    monkeypatch.setattr("smart_money.adapters.solana_rpc_fetcher.time.sleep", delays.append)
    fetcher = SolanaRPCFetcher(SolanaRPCConfig("https://example.invalid"), opener)
    with pytest.raises(OSError) as error:
        fetcher.capture_transaction("signature")
    assert "secret-url" not in str(error.value)
    assert len(calls) == attempts
    assert len(delays) == attempts - 1
    assert all(delay <= 10 for delay in delays)


def test_permanent_rpc_failure_not_retried(monkeypatch):
    fetcher = SolanaRPCFetcher(SolanaRPCConfig("https://example.invalid"))
    calls = []

    def fail(*args):
        calls.append(1)
        raise RuntimeError("Solana RPC error code: -32602")

    monkeypatch.setattr(fetcher, "request", fail)
    with pytest.raises(RuntimeError):
        fetcher.capture_transaction("signature")
    assert calls == [1]


def test_retry_policy_rejects_unbounded_settings():
    fetcher = SolanaRPCFetcher(SolanaRPCConfig("https://example.invalid"))
    for settings in ({"max_retries": 100}, {"base_delay": float("nan")}, {"base_delay": 99}):
        with pytest.raises(ValueError):
            fetcher.request_with_retry("getSlot", **settings)
