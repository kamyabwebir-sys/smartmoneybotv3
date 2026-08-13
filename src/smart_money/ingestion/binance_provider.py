from __future__ import annotations

import asyncio
from collections.abc import AsyncIterable, Sequence
from typing import Any

from .contracts import IngestionCandle, MarketSnapshot
from .errors import IngestionError, InvalidDataSchemaError
from .provider import BaseDataProvider


class BinanceProvider(BaseDataProvider):
    """Deterministic Binance mapping scaffold with bounded transient retries."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
        self._mock_data: list[Sequence[Any]] = []
        self._mock_snapshot_price: int | float | str = 0
        self._failure_count = 0

    def _map_candle(
        self,
        raw: Sequence[Any],
        *,
        symbol: str = "",
        interval: str = "",
    ) -> IngestionCandle:
        if len(raw) < 6:
            raise InvalidDataSchemaError(
                "Binance candle must contain at least six fields"
            )

        try:
            return IngestionCandle(
                timestamp=int(raw[0]),
                open=str(raw[1]),
                high=str(raw[2]),
                low=str(raw[3]),
                close=str(raw[4]),
                volume=str(raw[5]),
                symbol=symbol,
                interval=interval,
                source_id="binance",
            )
        except (TypeError, ValueError) as exc:
            raise InvalidDataSchemaError(f"Invalid Binance candle: {exc}") from exc

    async def get_candles(
        self,
        symbol: str,
        interval: str,
        limit: int,
    ) -> list[IngestionCandle]:
        max_retries = 3
        backoff_seconds = 0.1

        for attempt in range(max_retries):
            try:
                if self._failure_count > 0:
                    self._failure_count -= 1
                    raise ConnectionError("Temporary network failure.")

                return [
                    self._map_candle(raw, symbol=symbol, interval=interval)
                    for raw in self._mock_data[:limit]
                ]
            except ConnectionError as exc:
                if attempt == max_retries - 1:
                    raise IngestionError(
                        f"Failed after {max_retries} attempts: {exc}"
                    ) from exc
                await asyncio.sleep(backoff_seconds)
                backoff_seconds *= 2

        raise IngestionError("Binance retry loop terminated unexpectedly")

    async def stream_candles(
        self,
        symbol: str,
        interval: str,
    ) -> AsyncIterable[IngestionCandle]:
        if False:
            yield self._map_candle((), symbol=symbol, interval=interval)
        raise NotImplementedError("Streaming not implemented yet.")

    async def get_snapshot(self, symbol: str) -> MarketSnapshot:
        return MarketSnapshot(
            symbol=symbol,
            price=self._mock_snapshot_price,
            extra_metadata={"provider": "binance", "status": "active"},
        )
