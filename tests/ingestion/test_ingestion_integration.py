import pytest
from smart_money.ingestion.pipeline import IngestionPipeline
from smart_money.ingestion.binance_provider import BinanceProvider


@pytest.mark.asyncio
async def test_pipeline_to_provider_flow():
    # 1. Setup Provider with raw sample data
    provider = BinanceProvider()
    provider._mock_data = [
        [1625097600000, "35000.0", "35100.0", "34900.0", "35050.0", "10.0"],
        [1625097660000, "35050.0", "35200.0", "35000.0", "35150.0", "15.0"],
    ]

    # 2. Setup Pipeline
    pipeline = IngestionPipeline(provider=provider)

    # 3. Execute
    candles = await pipeline.ingest_historical("BTCUSDT", "1m", 2)

    # 4. Verify
    assert len(candles) == 2
    assert candles[0].open == 35000.0
    assert candles[1].close == 35150.0
    assert candles[1].timestamp == 1625097660000
