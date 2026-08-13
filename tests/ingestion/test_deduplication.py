from unittest.mock import AsyncMock, MagicMock

import pytest

from smart_money.ingestion.contracts import IngestionCandle
from smart_money.ingestion.pipeline import IngestionPipeline
from smart_money.ingestion.provider import BaseDataProvider


@pytest.mark.asyncio
async def test_deduplication_removes_repeats():
    # Setup
    mock_provider = MagicMock(spec=BaseDataProvider)
    # Return 3 candles, where middle one is a duplicate timestamp (100)
    mock_provider.get_candles = AsyncMock(
        return_value=[
            IngestionCandle(
                timestamp=100, open=1.0, high=2.0, low=0.5, close=1.5, volume=10.0
            ),
            IngestionCandle(
                timestamp=100, open=1.0, high=2.0, low=0.5, close=1.5, volume=10.0
            ),  # Dup
            IngestionCandle(
                timestamp=200, open=2.0, high=3.0, low=1.5, close=2.5, volume=20.0
            ),
        ]
    )

    pipeline = IngestionPipeline(provider=mock_provider)

    # Execute
    result = await pipeline.ingest_historical("TEST", "1m", 3)

    # Verify
    assert len(result) == 2
    assert result[0].timestamp == 100
    assert result[1].timestamp == 200
