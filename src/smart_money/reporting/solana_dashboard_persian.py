from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def build_persian_live_report(report: Mapping[str, Any]) -> dict[str, Any]:
    observations = report.get("normalized_observations", ())
    rows = observations if isinstance(observations, Sequence) else ()
    directions = {"BUY": 0, "SELL": 0, "UNKNOWN": 0}
    wallets: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        direction = str(row.get("direction", "UNKNOWN")).upper()
        directions[direction if direction in directions else "UNKNOWN"] += 1
        wallet = row.get("wallet")
        if isinstance(wallet, str) and wallet.strip():
            wallets.add(wallet.strip())
    gate = report.get("gate", {})
    gate_passed = isinstance(gate, Mapping) and gate.get("passed") is True
    candidate_count = int(report.get("candidate_count", 0))
    summaries = [
        f"در این نوبت {len(rows)} مشاهدهٔ استاندارد سولانا ثبت شده است.",
        f"تعداد سیگنال‌های خرید {directions['BUY']} و فروش {directions['SELL']} است.",
        f"سامانه {candidate_count} کاندید را برای بررسی انسانی ارائه کرده است.",
        "دروازهٔ عملیاتی عبور کرده است."
        if gate_passed
        else "دروازهٔ عملیاتی هنوز عبور نکرده و خروجی فقط پژوهشی است.",
    ]
    return {
        "schema_version": "persian_live_intelligence_report.v1",
        "title": "گزارش فارسی هوشمندی اسمارت‌مانی سولانا",
        "summary": tuple(summaries),
        "metrics": {
            "buy_count": directions["BUY"],
            "candidate_count": candidate_count,
            "observation_count": len(rows),
            "sell_count": directions["SELL"],
            "unknown_count": directions["UNKNOWN"],
            "wallet_count": len(wallets),
        },
        "warnings": (
            "این گزارش مجوز معامله یا توصیهٔ خرید نیست.",
            "موارد UNKNOWN باید با شواهد برنامه، pool و balance delta بازبینی شوند.",
        ),
        "read_only": True,
    }


__all__ = ["build_persian_live_report"]
