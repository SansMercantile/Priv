# backend/trading_engine/alerts_api.py

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

router = APIRouter()

# --- Mock Alert Data ---
# In a real system, these would come from your trading engine or alert service.
MOCK_ALERTS_DATA = [
    {"id": "alert_001", "type": "margin_call", "message": "Critical: Your margin is at 20%. Please deposit funds or close positions.", "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat()},
    {"id": "alert_002", "type": "price_target", "message": "Alert: Gold (GC=F) reached target price of $2350.00.", "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat()},
    {"id": "alert_003", "type": "news_event", "message": "Market Event: Key inflation data released. Expect volatility.", "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()},
    {"id": "alert_004", "type": "strategy_update", "message": "Strategy 'Phoenix' activated new risk-off parameters.", "timestamp": (datetime.now() - timedelta(hours=3)).isoformat()},
    {"id": "alert_005", "type": "info", "message": "Welcome back! Check out our new insights feature.", "timestamp": (datetime.now() - timedelta(days=1)).isoformat()},
]

@router.get("/alerts", response_model=List[Dict[str, Any]])
def get_recent_alerts() -> List[Dict[str, Any]]:
    """
    Retrieves a list of recent trade alerts.
    For demonstration, returns mock data. In a real app, this would fetch
    from a database or a real-time alert queue.
    """
    try:
        # Simulate occasional new alerts for dynamic behavior
        if random.random() < 0.3: # 30% chance of a new mock alert on refresh
            new_alert_id = f"alert_{len(MOCK_ALERTS_DATA) + 1:03d}"
            new_alert_type = random.choice(["margin_call", "price_target", "news_event", "info"])
            new_alert_message = f"Simulated new alert: {new_alert_type} triggered at {datetime.now().strftime('%H:%M:%S')}"
            MOCK_ALERTS_DATA.insert(0, { # Add to the beginning to show as newest
                "id": new_alert_id,
                "type": new_alert_type,
                "message": new_alert_message,
                "timestamp": datetime.now().isoformat()
            })

        # Return a subset or all, newest first
        return sorted(MOCK_ALERTS_DATA, key=lambda x: x['timestamp'], reverse=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts: {e}")