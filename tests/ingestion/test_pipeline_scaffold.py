from unittest.mock import AsyncMock, MagicMock

import pytest

from smart_money.ingestion.contracts import IngestionCandle
from smart_money.ingestion.errors import IngestionError
from smart_money.ingestion.pipeline import IngestionPipeline
from smart_money.ingestion.provider import BaseDataProvider


@pytest.mark.asyncio
async def test_pipeline_wraps_exceptions():
    mock_provider = MagicMock(spec=BaseDataProvider)
    mock_provider.get_candles = AsyncMock(side_effect=ValueError("Raw API Error"))

    pipeline = IngestionPipeline(provider=mock_provider)
    with pytest.raises(IngestionError) as exc:
        await pipeline.ingest_historical("SOL", "1m", 10)
    assert "Pipeline failure" in str(exc.value)


@pytest.mark.asyncio
async def test_pipeline_success():
    mock_provider = MagicMock(spec=BaseDataProvider)
    mock_provider.get_candles = AsyncMock(
        return_value=[
            IngestionCandle(
                timestamp=1,
                open="100",
                high="110",
                low="90",
                close="105",
                volume="10",
            )
        ]
    )

    pipeline = IngestionPipeline(provider=mock_provider)
    result = await pipeline.ingest_historical("SOL", "1m", 1)
    assert len(result) == 1
