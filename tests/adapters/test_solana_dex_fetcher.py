from __future__ import annotations

import importlib

import pytest

from smart_money.adapters.persistence.durable_json_ledger import (
    DurableJsonEvidenceLedger,
)
from smart_money.adapters.solana_dex_fetcher import DexFetchOptions, fetch_dex_swaps
from tests.adapters.test_solana_signature_normalizer import _buy_payload

WALLET = "9HCTuTPEiQvkUtLmTZvK6uch4E3pDynwJTbNw6jLhp9z"
OTHER_WALLET = "5fWkLJfoDsRAaXhPJcJY19qNtDDQ5h6q1SPzsAPRrUNG"


def _signature(marker: str) -> str:
    return (marker * 88)[:88]


def _transaction(signature: str, *, wallet: str = WALLET, direction: str = "BUY"):
    payload = _buy_payload()
    payload["transaction"]["signatures"] = [signature]  # type: ignore[index]
    payload["transaction"]["message"]["accountKeys"][0]["pubkey"] = wallet  # type: ignore[index]
    for side in ("preTokenBalances", "postTokenBalances"):
        for row in payload["meta"][side]:  # type: ignore[index]
            row["owner"] = wallet
    if direction == "SELL":
        payload["meta"]["preTokenBalances"], payload["meta"]["postTokenBalances"] = (  # type: ignore[index]
            payload["meta"]["postTokenBalances"],  # type: ignore[index]
            payload["meta"]["preTokenBalances"],  # type: ignore[index]
        )
        payload["meta"]["preBalances"] = [1_999_995_000]  # type: ignore[index]
        payload["meta"]["postBalances"] = [2_000_000_000]  # type: ignore[index]
    elif direction == "UNKNOWN":
        payload["meta"]["postTokenBalances"] = payload["meta"]["preTokenBalances"]  # type: ignore[index]
    return {"jsonrpc": "2.0", "id": 1, "result": payload}


class FakeRPC:
    def __init__(self, pages, transactions):
        self.pages = list(pages)
        self.transactions = transactions
        self.before_values = []

    def capture_signatures(self, address, limit=20, before=None):
        self.before_values.append(before)
        return {"result": self.pages.pop(0) if self.pages else []}

    def capture_transaction(self, signature):
        value = self.transactions[signature]
        if isinstance(value, BaseException):
            raise value
        return value


def test_options_allow_missing_wallet_and_reject_invalid_wallet() -> None:
    assert DexFetchOptions(wallet=None).wallet is None
    with pytest.raises(ValueError, match="Base58"):
        DexFetchOptions(wallet="not-a-wallet")


def test_fetch_is_signer_centric_filters_unknown_and_binds_ledger(tmp_path) -> None:
    buy, sell, unknown, other = map(_signature, "2345")
    rows = [{"signature": item} for item in (buy, sell, unknown, other)]
    rpc = FakeRPC(
        [rows],
        {
            buy: _transaction(buy),
            sell: _transaction(sell, direction="SELL"),
            unknown: _transaction(unknown, direction="UNKNOWN"),
            other: _transaction(other, wallet=OTHER_WALLET),
        },
    )
    ledger = DurableJsonEvidenceLedger(tmp_path / "ledger.json")

    report = fetch_dex_swaps(
        rpc,
        DexFetchOptions(limit=2, scan_limit=10, wallet=WALLET),
        ledger=ledger,
    )

    assert tuple(row.direction for row in report.records) == ("BUY", "SELL")
    assert report.rejected_unknown == 0
    assert report.rejected_non_signer == 0
    assert ledger.entry_count == 2
    assert all(row.evidence_id for row in report.records)


def test_failed_unknown_and_non_signer_are_rejected() -> None:
    failed, unknown, other = map(_signature, "678")
    failed_tx = _transaction(failed)
    failed_tx["result"]["meta"]["err"] = {"InstructionError": [1, "Custom"]}
    rpc = FakeRPC(
        [[{"signature": failed}, {"signature": unknown}, {"signature": other}]],
        {
            failed: failed_tx,
            unknown: _transaction(unknown, direction="UNKNOWN"),
            other: _transaction(other, wallet=OTHER_WALLET),
        },
    )
    report = fetch_dex_swaps(
        rpc, DexFetchOptions(limit=3, scan_limit=3, wallet=WALLET)
    )
    assert not report.records
    assert (report.rejected_failed, report.rejected_unknown, report.rejected_non_signer) == (1, 1, 1)
    assert report.rejected_rpc == 0


def test_pagination_advances_and_rpc_failure_is_accounted_for() -> None:
    first, second = _signature("9"), _signature("a")
    safe_markers = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    first_page = [
        {"signature": _signature(safe_markers[index % len(safe_markers)])}
        for index in range(100)
    ]
    first_page[-1] = {"signature": first}
    transactions = {
        row["signature"]: _transaction(row["signature"], direction="UNKNOWN")
        for row in first_page
    }
    transactions[second] = _transaction(second)
    rpc = FakeRPC(
        [first_page, [{"signature": second}]],
        transactions,
    )
    report = fetch_dex_swaps(rpc, DexFetchOptions(limit=1, scan_limit=101))
    assert report.records[0].signature == second
    assert rpc.before_values == [None, first]

    failing = FakeRPC([[{"signature": first}]], {first: OSError("rpc down")})
    failure_report = fetch_dex_swaps(
        failing, DexFetchOptions(limit=1, scan_limit=1)
    )
    assert failure_report.rejected_rpc == 1
    assert not failure_report.records


def test_runtime_rpc_rejection_does_not_abort_remaining_transactions() -> None:
    failed, successful = _signature("b"), _signature("c")
    rpc = FakeRPC(
        [[{"signature": failed}, {"signature": successful}]],
        {
            failed: RuntimeError("unsupported transaction version"),
            successful: _transaction(successful),
        },
    )

    report = fetch_dex_swaps(rpc, DexFetchOptions(limit=1, scan_limit=2))

    assert report.records[0].signature == successful
    assert report.rejected_rpc == 1


def test_compatibility_wrapper_is_safe_to_import() -> None:
    module = importlib.import_module("scripts.fetch_dex_swaps_final")
    assert callable(module.deprecated_main)
