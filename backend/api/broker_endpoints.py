# backend/api/broker_endpoints.py
"""
FastAPI endpoints for broker management.

Provides REST API for:
- Registering and managing broker connections
- Executing trades across multiple brokers
- Monitoring positions and orders
- Retrieving market data
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..trading_engine.broker_api import broker_manager, BrokerType

router = APIRouter(prefix="/api/brokers", tags=["Brokers"])


# Pydantic models for request/response
class BrokerRegistrationRequest(BaseModel):
    """Request model for registering a new broker"""
    broker_id: str = Field(..., description="Unique identifier for this broker connection")
    broker_type: BrokerType = Field(..., description="Type of broker (ib, alpaca, binance, etc.)")
    config: Dict[str, Any] = Field(..., description="Broker-specific configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "broker_id": "ib_paper_1",
                "broker_type": "ib",
                "config": {
                    "host": "127.0.0.1",
                    "port": 7497,
                    "client_id": 1,
                    "readonly": False
                }
            }
        }


class TradeExecutionRequest(BaseModel):
    """Request model for executing a trade"""
    broker_id: str = Field(..., description="Broker to execute on")
    order_type: str = Field(..., description="Order type (MARKET, LIMIT, STOP, etc.)")
    symbol: str = Field(..., description="Trading symbol")
    volume: float = Field(..., description="Order volume (positive for buy, negative for sell)")
    price: Optional[float] = Field(None, description="Limit price (if applicable)")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    
    class Config:
        json_schema_extra = {
            "example": {
                "broker_id": "ib_paper_1",
                "order_type": "MARKET",
                "symbol": "AAPL",
                "volume": 100,
                "stop_loss": 145.00,
                "take_profit": 160.00
            }
        }


class ClosePositionRequest(BaseModel):
    """Request model for closing a position"""
    broker_id: str = Field(..., description="Broker ID")
    symbol: str = Field(..., description="Symbol to close")
    volume: Optional[float] = Field(None, description="Volume to close (None for full position)")


class CancelOrderRequest(BaseModel):
    """Request model for cancelling an order"""
    broker_id: str = Field(..., description="Broker ID")
    order_id: Union[int, str] = Field(..., description="Order ID to cancel")


class HistoricalDataRequest(BaseModel):
    """Request model for historical data"""
    broker_id: str = Field(..., description="Broker ID")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe (M1, M5, H1, D1, etc.)")
    limit: int = Field(100, description="Number of bars to fetch")


# Endpoints
@router.post("/register", response_model=Dict[str, Any])
async def register_broker(request: BrokerRegistrationRequest):
    """
    Register a new broker connection.
    
    Supported broker types:
    - ib: Interactive Brokers
    - alpaca: Alpaca Markets
    - binance: Binance
    - deriv: Deriv
    - mt5: MetaTrader 5
    """
    success = await broker_manager.register_broker(
        broker_id=request.broker_id,
        broker_type=request.broker_type,
        config=request.config
    )
    
    if success:
        return {
            "success": True,
            "message": f"Broker {request.broker_id} registered successfully",
            "broker_id": request.broker_id
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to register broker")


@router.post("/connect/{broker_id}", response_model=Dict[str, Any])
async def connect_broker(broker_id: str):
    """Connect to a registered broker."""
    success = await broker_manager.connect_broker(broker_id)
    
    if success:
        return {
            "success": True,
            "message": f"Connected to broker {broker_id}",
            "broker_id": broker_id
        }
    else:
        raise HTTPException(status_code=400, detail=f"Failed to connect to broker {broker_id}")


@router.post("/disconnect/{broker_id}", response_model=Dict[str, Any])
async def disconnect_broker(broker_id: str):
    """Disconnect from a broker."""
    success = await broker_manager.disconnect_broker(broker_id)
    
    if success:
        return {
            "success": True,
            "message": f"Disconnected from broker {broker_id}",
            "broker_id": broker_id
        }
    else:
        raise HTTPException(status_code=400, detail=f"Failed to disconnect from broker {broker_id}")


@router.get("/status", response_model=List[Dict[str, Any]])
async def get_all_brokers_status():
    """Get status of all registered brokers."""
    return await broker_manager.get_all_brokers_status()


@router.get("/status/{broker_id}", response_model=Dict[str, Any])
async def get_broker_status(broker_id: str):
    """Get status of a specific broker."""
    status = await broker_manager.get_broker_status(broker_id)
    
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    
    return status


@router.get("/account/{broker_id}", response_model=Dict[str, Any])
async def get_account_info(broker_id: str):
    """Get account information from a specific broker."""
    account_info = await broker_manager.get_account_info(broker_id)

    if "error" in account_info:
        raise HTTPException(status_code=400, detail=account_info["error"])

    return account_info


@router.get("/portfolio", response_model=Dict[str, Any])
async def get_aggregated_portfolio():
    """Get aggregated portfolio across all connected brokers."""
    return await broker_manager.get_aggregated_portfolio()


@router.get("/positions", response_model=List[Dict[str, Any]])
async def get_all_positions(broker_id: Optional[str] = None):
    """
    Get all open positions.

    Args:
        broker_id: Optional broker ID to filter positions
    """
    return await broker_manager.get_all_positions(broker_id)


@router.get("/orders", response_model=List[Dict[str, Any]])
async def get_all_orders(broker_id: Optional[str] = None):
    """
    Get all pending orders.

    Args:
        broker_id: Optional broker ID to filter orders
    """
    return await broker_manager.get_all_orders(broker_id)


@router.post("/trade", response_model=Dict[str, Any])
async def execute_trade(request: TradeExecutionRequest):
    """
    Execute a trade on a specific broker.

    Supported order types:
    - MARKET: Market order
    - LIMIT: Limit order
    - STOP: Stop order
    - STOP_LIMIT: Stop-limit order
    - TRAILING_STOP: Trailing stop order
    """
    result = await broker_manager.execute_trade(
        broker_id=request.broker_id,
        order_type=request.order_type,
        symbol=request.symbol,
        volume=request.volume,
        price=request.price,
        stop_loss=request.stop_loss,
        take_profit=request.take_profit
    )

    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Trade execution failed"))

    return result


@router.post("/close-position", response_model=Dict[str, Any])
async def close_position(request: ClosePositionRequest):
    """Close a position on a specific broker."""
    result = await broker_manager.close_position(
        broker_id=request.broker_id,
        symbol=request.symbol,
        volume=request.volume
    )

    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to close position"))

    return result


@router.post("/cancel-order", response_model=Dict[str, Any])
async def cancel_order(request: CancelOrderRequest):
    """Cancel a pending order."""
    result = await broker_manager.cancel_order(
        broker_id=request.broker_id,
        order_id=request.order_id
    )

    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to cancel order"))

    return result


@router.post("/historical-data", response_model=Dict[str, Any])
async def get_historical_data(request: HistoricalDataRequest):
    """Get historical market data from a broker."""
    df = await broker_manager.get_historical_data(
        broker_id=request.broker_id,
        symbol=request.symbol,
        timeframe=request.timeframe,
        limit=request.limit
    )

    if df is None:
        raise HTTPException(status_code=400, detail="Failed to fetch historical data")

    # Convert DataFrame to dict for JSON response
    return {
        "symbol": request.symbol,
        "timeframe": request.timeframe,
        "bars": df.to_dict(orient="records") if hasattr(df, 'to_dict') else [],
        "count": len(df) if hasattr(df, '__len__') else 0
    }


@router.get("/registered", response_model=List[str])
async def get_registered_brokers():
    """Get list of all registered broker IDs."""
    return broker_manager.get_registered_brokers()


@router.get("/connected", response_model=List[str])
async def get_connected_brokers():
    """Get list of all connected broker IDs."""
    return broker_manager.get_connected_brokers()


@router.post("/disconnect-all", response_model=Dict[str, Any])
async def disconnect_all_brokers():
    """Disconnect from all brokers."""
    await broker_manager.disconnect_all()
    return {
        "success": True,
        "message": "Disconnected from all brokers"
    }


# Health check endpoint
@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint for broker management API."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "registered_brokers": len(broker_manager.get_registered_brokers()),
        "connected_brokers": len(broker_manager.get_connected_brokers())
    }

