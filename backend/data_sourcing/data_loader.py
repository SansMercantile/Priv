# backend/data_sourcing/data_loader.py
import pandas as pd
import logging
from typing import Optional

from backend.trading_engine.broker_router import broker_router

logger = logging.getLogger(__name__)

async def get_market_data(
    symbol: str, 
    timeframe: str = "daily", 
    num_bars: int = 250
) -> Optional[pd.DataFrame]:
    """
    Fetches historical market data from the best available live broker adapter.
    """
    logger.info(f"Attempting to fetch {num_bars} bars for {symbol} ({timeframe}) from live broker...")
    
    try:
        active_adapter = await broker_router.select_adapter()
        if not active_adapter:
            logger.error("No active broker adapter found to fetch market data.")
            return None

        historical_df = await active_adapter.get_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            limit=num_bars
        )

        if historical_df is None or historical_df.empty:
            logger.warning(f"Adapter '{active_adapter.name}' returned no data for {symbol}.")
            return None

        logger.info(f"Successfully fetched {len(historical_df)} bars for {symbol} via '{active_adapter.name}'.")
        
        historical_df.columns = [col.lower() for col in historical_df.columns]
        historical_df.index.name = 'timestamp'
        
        return historical_df

    except Exception as e:
        logger.error(f"An unexpected error occurred in get_market_data: {e}", exc_info=True)
        return None