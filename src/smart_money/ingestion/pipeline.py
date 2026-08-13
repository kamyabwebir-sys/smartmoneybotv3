from __future__ import annotations

from .contracts import IngestionCandle, MarketSnapshot
from .errors import IngestionError, InvalidDataSchemaError
from .provider import BaseDataProvider


class IngestionPipeline:
    """Coordinate provider reads without defining analytical truth."""

    def __init__(self, provider: BaseDataProvider) -> None:
        self.provider = provider
        self._seen_candles: set[tuple[str, str, int | object]] = set()

    async def ingest_historical(
        self,
        symbol: str,
        interval: str,
        limit: int,
    ) -> list[IngestionCandle]:
        if not isinstance(symbol, str) or not symbol.strip():
            raise InvalidDataSchemaError("symbol must be a non-empty string")
        if not isinstance(interval, str) or not interval.strip():
            raise InvalidDataSchemaError("interval must be a non-empty string")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise InvalidDataSchemaError("limit must be a positive integer")

        try:
            candles = await self.provider.get_candles(
                symbol.strip(),
                interval.strip(),
                limit,
            )
            unique_candles: list[IngestionCandle] = []
            for candle in candles:
                if not isinstance(candle, IngestionCandle):
                    raise InvalidDataSchemaError(
                        "provider returned a non-IngestionCandle item"
                    )

                identity = (symbol.strip(), interval.strip(), candle.timestamp)
                if identity in self._seen_candles:
                    continue
                self._seen_candles.add(identity)
                unique_candles.append(candle)
            return unique_candles
        except Exception as exc:
            if isinstance(exc, IngestionError) and str(exc).startswith(
                "Pipeline failure:"
            ):
                raise
            raise IngestionError(f"Pipeline failure: {exc}") from exc

    async def get_current_state(self, symbol: str) -> MarketSnapshot:
        if not isinstance(symbol, str) or not symbol.strip():
            raise InvalidDataSchemaError("symbol must be a non-empty string")

        try:
            snapshot = await self.provider.get_snapshot(symbol.strip())
            if not isinstance(snapshot, MarketSnapshot):
                raise InvalidDataSchemaError(
                    "provider returned a non-MarketSnapshot value"
                )
            return snapshot
        except Exception as exc:
            if isinstance(exc, IngestionError) and str(exc).startswith(
                "Pipeline failure:"
            ):
                raise
            raise IngestionError(f"Pipeline failure: {exc}") from exc
