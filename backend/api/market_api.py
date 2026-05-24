"""
Market data API endpoints for PRIV backend.
Provides market quotes, charts, and related data.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/data")
async def get_market_data(symbols: Optional[str] = Query(None)) -> Dict[str, Any]:
    """
    Get market data for specified symbols.
    Returns mock data for now.
    
    Args:
        symbols: Comma-separated list of stock symbols (e.g., "AAPL,MSFT,GOOGL")
    """
    try:
        # Parse symbols
        symbol_list = symbols.split(",") if symbols else ["AAPL", "MSFT", "GOOGL"]
        symbol_list = [s.strip().upper() for s in symbol_list if s.strip()]
        
        # Mock market data
        mock_data = {
            "AAPL": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "price": 175.00,
                "change": 2.50,
                "change_pct": 1.45,
                "volume": 50234567,
                "high": 177.50,
                "low": 173.00,
                "open": 174.00,
                "prev_close": 172.50
            },
            "MSFT": {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "price": 350.00,
                "change": 5.00,
                "change_pct": 1.45,
                "volume": 25123456,
                "high": 352.00,
                "low": 348.00,
                "open": 349.00,
                "prev_close": 345.00
            },
            "GOOGL": {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "price": 140.00,
                "change": 1.50,
                "change_pct": 1.08,
                "volume": 20456789,
                "high": 141.00,
                "low": 138.50,
                "open": 139.00,
                "prev_close": 138.50
            }
        }
        
        # Get data for requested symbols
        quotes = []
        for symbol in symbol_list:
            if symbol in mock_data:
                quotes.append(mock_data[symbol])
            else:
                # Return mock data for unknown symbols
                quotes.append({
                    "symbol": symbol,
                    "name": f"{symbol} Company",
                    "price": 100.00,
                    "change": 0.00,
                    "change_pct": 0.00,
                    "volume": 1000000,
                    "high": 100.00,
                    "low": 100.00,
                    "open": 100.00,
                    "prev_close": 100.00
                })
        
        indices = [
            {
                "symbol": "^GSPC",
                "name": "S&P 500",
                "value": 4750.00,
                "change": 25.50,
                "change_pct": 0.54
            },
            {
                "symbol": "^DJI",
                "name": "Dow Jones Industrial Average",
                "value": 37500.00,
                "change": 150.00,
                "change_pct": 0.40
            },
            {
                "symbol": "^IXIC",
                "name": "NASDAQ Composite",
                "value": 15000.00,
                "change": 100.00,
                "change_pct": 0.67
            }
        ]

        return {
            "success": True,
            "data": {
                "quotes": quotes,
                "indices": indices,
                "alerts": [
                    {
                        "severity": "info",
                        "message": f"Monitoring {len(symbol_list)} symbol(s) for intraday volatility.",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ],
                "sentiment": "neutral",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quotes")
async def get_market_quotes(symbols: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Alias endpoint used by some frontend services."""
    return await get_market_data(symbols)


@router.get("/indices")
async def get_market_indices() -> Dict[str, Any]:
    """
    Get major market indices data.
    Returns mock data for now.
    """
    try:
        return {
            "success": True,
            "data": {
                "indices": [
                    {
                        "symbol": "^GSPC",
                        "name": "S&P 500",
                        "value": 4750.00,
                        "change": 25.50,
                        "change_pct": 0.54
                    },
                    {
                        "symbol": "^DJI",
                        "name": "Dow Jones Industrial Average",
                        "value": 37500.00,
                        "change": 150.00,
                        "change_pct": 0.40
                    },
                    {
                        "symbol": "^IXIC",
                        "name": "NASDAQ Composite",
                        "value": 15000.00,
                        "change": 100.00,
                        "change_pct": 0.67
                    }
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error fetching market indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))
