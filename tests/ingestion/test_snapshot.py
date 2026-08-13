import pytest

from smart_money.ingestion.binance_provider import BinanceProvider
from smart_money.ingestion.pipeline import IngestionPipeline


@pytest.mark.asyncio
async def test_get_snapshot_flow():
    # Setup
    provider = BinanceProvider()
    provider._mock_snapshot_price = 45000.5
    pipeline = IngestionPipeline(provider=provider)

    # Execute
    snapshot = await pipeline.get_current_state("BTCUSDT")

    # Verify
    assert snapshot.symbol == "BTCUSDT"
    assert snapshot.price == 45000.5
    assert snapshot.extra_metadata["provider"] == "binance"
