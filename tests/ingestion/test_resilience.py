import pytest
from smart_money.ingestion.binance_provider import BinanceProvider
from smart_money.ingestion.pipeline import IngestionPipeline
from smart_money.ingestion.errors import IngestionError


@pytest.mark.asyncio
async def test_pipeline_recovers_from_temporary_failures():
    # Setup Provider with 2 failures, then success
    provider = BinanceProvider()
    provider._failure_count = 2
    provider._mock_data = [
        [1625097600000, "35000.0", "35100.0", "34900.0", "35050.0", "10.0"]
    ]

    pipeline = IngestionPipeline(provider=provider)

    # Execute (should fail twice, wait/backoff, then succeed on 3rd attempt)
    candles = await pipeline.ingest_historical("BTCUSDT", "1m", 1)

    # Verify
    assert len(candles) == 1
    assert candles[0].close == 35050.0
    assert provider._failure_count == 0


@pytest.mark.asyncio
async def test_pipeline_fails_after_max_retries():
    # Setup Provider with 4 failures (exceeds max_retries=3)
    provider = BinanceProvider()
    provider._failure_count = 4
    pipeline = IngestionPipeline(provider=provider)

    # Verify IngestionError is raised
    with pytest.raises(IngestionError):
        await pipeline.ingest_historical("BTCUSDT", "1m", 1)
