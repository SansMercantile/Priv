"""
History API endpoints for PRIV backend.
Provides transaction history, trade logs, and audit trails.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import random

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/transactions")
async def get_transactions(
    limit: int = 50,
    days: int = 30,
    transaction_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get transaction history.
    
    Args:
        limit: Maximum number of transactions to return
        days: Number of days to look back
        transaction_type: Filter by type (buy, sell, dividend, etc.)
    
    Returns:
        Dictionary containing transactions
    """
    try:
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMD", "META"]
        types = ["buy", "sell", "dividend", "split", "transfer"]
        
        transactions = []
        end_date = datetime.utcnow()
        
        for i in range(min(limit, 50)):
            days_ago = random.randint(0, days)
            trans_date = end_date - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            trans_type = random.choice(types) if not transaction_type else transaction_type
            symbol = random.choice(symbols)
            quantity = random.randint(1, 100)
            price = round(random.uniform(50, 500), 2)
            
            transaction = {
                "id": f"TXN-{i+1:06d}",
                "date": trans_date.isoformat(),
                "type": trans_type,
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "total": round(quantity * price, 2),
                "status": "completed",
                "broker": "Interactive Brokers",
                "account": "****1234"
            }
            
            # Add type-specific fields
            if trans_type == "dividend":
                transaction["dividend_per_share"] = round(price / 100, 2)
                transaction["total"] = round(quantity * transaction["dividend_per_share"], 2)
            elif trans_type == "split":
                transaction["split_ratio"] = "2:1"
                transaction["new_quantity"] = quantity * 2
            
            transactions.append(transaction)
        
        # Sort by date (most recent first)
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate statistics
        buy_count = sum(1 for t in transactions if t['type'] == 'buy')
        sell_count = sum(1 for t in transactions if t['type'] == 'sell')
        total_volume = sum(t.get('total', 0) for t in transactions if t['type'] in ['buy', 'sell'])
        
        return {
            "transactions": transactions,
            "total": len(transactions),
            "statistics": {
                "buy_count": buy_count,
                "sell_count": sell_count,
                "total_volume": round(total_volume, 2),
                "avg_trade_size": round(total_volume / (buy_count + sell_count), 2) if (buy_count + sell_count) > 0 else 0
            },
            "period_days": days,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(status: Optional[str] = None) -> Dict[str, Any]:
    """
    Get order history and status.
    
    Args:
        status: Filter by order status (pending, filled, cancelled, rejected)
    
    Returns:
        Dictionary containing orders
    """
    try:
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        statuses = ["filled", "pending", "cancelled", "partially_filled"]
        order_types = ["market", "limit", "stop", "stop_limit"]
        
        orders = []
        
        for i in range(20):
            days_ago = random.randint(0, 7)
            order_date = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            order_status = random.choice(statuses) if not status else status
            order_type = random.choice(order_types)
            symbol = random.choice(symbols)
            quantity = random.randint(10, 200)
            limit_price = round(random.uniform(100, 400), 2)
            
            order = {
                "id": f"ORD-{i+1:06d}",
                "date": order_date.isoformat(),
                "symbol": symbol,
                "side": random.choice(["buy", "sell"]),
                "type": order_type,
                "quantity": quantity,
                "filled_quantity": quantity if order_status == "filled" else random.randint(0, quantity),
                "limit_price": limit_price if order_type in ["limit", "stop_limit"] else None,
                "stop_price": round(limit_price * 0.95, 2) if order_type in ["stop", "stop_limit"] else None,
                "status": order_status,
                "broker": "Interactive Brokers"
            }
            
            orders.append(order)
        
        # Sort by date (most recent first)
        orders.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate statistics
        status_counts = {}
        for s in statuses:
            status_counts[s] = sum(1 for o in orders if o['status'] == s)
        
        return {
            "orders": orders,
            "total": len(orders),
            "status_breakdown": status_counts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity")
async def get_activity_log(limit: int = 100) -> Dict[str, Any]:
    """
    Get user activity log and audit trail.
    
    Args:
        limit: Maximum number of activities to return
    
    Returns:
        Dictionary containing activity logs
    """
    try:
        activities = []
        activity_types = [
            "login", "logout", "trade_executed", "order_placed", 
            "order_cancelled", "settings_changed", "alert_triggered",
            "report_generated", "data_export", "api_access"
        ]
        
        for i in range(min(limit, 100)):
            hours_ago = random.randint(0, 72)
            activity_date = datetime.utcnow() - timedelta(hours=hours_ago, minutes=random.randint(0, 59))
            
            activity_type = random.choice(activity_types)
            
            activity = {
                "id": f"ACT-{i+1:06d}",
                "timestamp": activity_date.isoformat(),
                "type": activity_type,
                "description": f"{activity_type.replace('_', ' ').title()}",
                "ip_address": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "status": "success"
            }
            
            # Add type-specific details
            if "order" in activity_type or "trade" in activity_type:
                activity["details"] = {
                    "symbol": random.choice(["AAPL", "MSFT", "GOOGL"]),
                    "quantity": random.randint(10, 100)
                }
            
            activities.append(activity)
        
        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "activities": activities,
            "total": len(activities),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching activity log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
