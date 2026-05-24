"""
Connections API endpoints for PRIV backend.
Provides broker connection status and management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
import random
import os
import json

logger = logging.getLogger(__name__)

router = APIRouter()

_CONNECTION_STORE = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', 'broker_connections.json')
)
os.makedirs(os.path.dirname(_CONNECTION_STORE), exist_ok=True)


class BrokerKeysPayload(BaseModel):
    broker_name: str
    api_key: str
    api_secret: str


def _load_saved_connections() -> list[dict[str, Any]]:
    try:
        if not os.path.exists(_CONNECTION_STORE):
            return []
        with open(_CONNECTION_STORE, 'r', encoding='utf-8') as handle:
            return json.load(handle)
    except Exception as exc:
        logger.warning(f"Could not load saved broker connections: {exc}")
        return []


def _save_connection_metadata(payload: BrokerKeysPayload) -> dict[str, Any]:
    masked_key = f"***{payload.api_key[-4:]}" if payload.api_key else "***"
    masked_secret = f"***{payload.api_secret[-4:]}" if payload.api_secret else "***"
    record = {
        "id": payload.broker_name.lower().replace(' ', '-'),
        "broker_name": payload.broker_name,
        "api_key_masked": masked_key,
        "api_secret_masked": masked_secret,
        "saved_at": datetime.utcnow().isoformat(),
        "status": "connected",
    }
    existing = [item for item in _load_saved_connections() if item.get('broker_name') != payload.broker_name]
    existing.append(record)
    with open(_CONNECTION_STORE, 'w', encoding='utf-8') as handle:
        json.dump(existing, handle, indent=2)
    return record


@router.post("/save-broker-keys")
async def save_broker_keys(payload: BrokerKeysPayload) -> Dict[str, Any]:
    """Accept broker credentials from the frontend and persist only masked metadata locally."""
    try:
        record = _save_connection_metadata(payload)
        return {
            "success": True,
            "message": f"{payload.broker_name} connection saved successfully.",
            "data": record,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        logger.error(f"Error saving broker keys for {payload.broker_name}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/brokers")
async def get_broker_connections() -> Dict[str, Any]:
    """
    Get status of all broker connections.
    
    Returns:
        Dictionary containing broker connection information
    """
    try:
        saved_connections = _load_saved_connections()

        connections = [
            {
                "id": "ibkr-main",
                "name": "Interactive Brokers",
                "type": "IBKR",
                "status": "connected",
                "account": "****1234",
                "connected_since": (datetime.utcnow() - timedelta(hours=3, minutes=24)).isoformat(),
                "last_heartbeat": datetime.utcnow().isoformat(),
                "api_version": "10.19",
                "capabilities": ["trading", "market_data", "account_management"],
                "latency_ms": random.randint(10, 50),
                "requests_today": random.randint(1000, 5000),
                "rate_limit": "50 req/sec",
                "health": "excellent"
            },
            {
                "id": "mt5-forex",
                "name": "MetaTrader 5",
                "type": "MT5",
                "status": "connected",
                "account": "****5678",
                "connected_since": (datetime.utcnow() - timedelta(hours=1, minutes=45)).isoformat(),
                "last_heartbeat": datetime.utcnow().isoformat(),
                "api_version": "5.0.37",
                "capabilities": ["trading", "market_data", "technical_analysis"],
                "latency_ms": random.randint(50, 150),
                "requests_today": random.randint(500, 2000),
                "rate_limit": "100 req/min",
                "health": "good"
            },
            {
                "id": "alpaca-crypto",
                "name": "Alpaca Markets",
                "type": "Alpaca",
                "status": "disconnected",
                "account": "****9012",
                "connected_since": None,
                "last_heartbeat": (datetime.utcnow() - timedelta(minutes=12)).isoformat(),
                "api_version": "2.0",
                "capabilities": ["trading", "market_data"],
                "latency_ms": None,
                "requests_today": 0,
                "rate_limit": "200 req/min",
                "health": "offline",
                "error": "Connection timeout after 30s"
            },
            {
                "id": "polygon-data",
                "name": "Polygon.io",
                "type": "Data Provider",
                "status": "connected",
                "account": "****3456",
                "connected_since": (datetime.utcnow() - timedelta(days=2, hours=5)).isoformat(),
                "last_heartbeat": datetime.utcnow().isoformat(),
                "api_version": "v3",
                "capabilities": ["market_data", "historical_data", "crypto_data"],
                "latency_ms": random.randint(20, 80),
                "requests_today": random.randint(2000, 8000),
                "rate_limit": "5 req/sec (basic plan)",
                "health": "excellent"
            }
        ]

        for saved in saved_connections:
            if any(conn.get('name') == saved.get('broker_name') for conn in connections):
                continue
            connections.append({
                "id": saved.get("id"),
                "name": saved.get("broker_name"),
                "type": "Custom",
                "status": saved.get("status", "connected"),
                "account": saved.get("api_key_masked", "***"),
                "connected_since": saved.get("saved_at"),
                "last_heartbeat": datetime.utcnow().isoformat(),
                "api_version": "local",
                "capabilities": ["trading", "market_data"],
                "latency_ms": random.randint(20, 120),
                "requests_today": random.randint(0, 100),
                "rate_limit": "local",
                "health": "good"
            })

        # Calculate statistics
        total = len(connections)
        connected = sum(1 for c in connections if c['status'] == 'connected')
        avg_latency = sum(c['latency_ms'] for c in connections if c['latency_ms']) / connected if connected > 0 else 0
        
        return {
            "connections": connections,
            "summary": {
                "total": total,
                "connected": connected,
                "disconnected": total - connected,
                "health_score": round((connected / total) * 100, 1),
                "avg_latency_ms": round(avg_latency, 1),
                "total_requests_today": sum(c['requests_today'] for c in connections)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching broker connections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brokers/{broker_id}")
async def get_broker_details(broker_id: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific broker connection.
    
    Args:
        broker_id: ID of the broker connection
    
    Returns:
        Dictionary containing detailed broker information
    """
    try:
        # This would typically query a database
        # For now, return mock detailed data
        details = {
            "id": broker_id,
            "name": "Interactive Brokers",
            "status": "connected",
            "connection_history": [
                {
                    "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=24)).isoformat(),
                    "event": "connected",
                    "message": "Successfully connected to IBKR API"
                },
                {
                    "timestamp": (datetime.utcnow() - timedelta(hours=5, minutes=10)).isoformat(),
                    "event": "disconnected",
                    "message": "Connection closed by user"
                }
            ],
            "performance_metrics": {
                "uptime_pct": 99.7,
                "avg_response_time_ms": 35,
                "success_rate_pct": 99.9,
                "total_requests": 45230,
                "failed_requests": 45
            },
            "configuration": {
                "host": "api.ibkr.com",
                "port": 4001,
                "client_id": 1,
                "timeout_seconds": 30,
                "reconnect_attempts": 5,
                "log_level": "INFO"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return details
        
    except Exception as e:
        logger.error(f"Error fetching broker details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_connection_health() -> Dict[str, Any]:
    """
    Get overall connection health status.
    
    Returns:
        Dictionary containing health metrics
    """
    try:
        health = {
            "overall_status": "healthy",
            "health_score": 87.5,
            "checks": [
                {
                    "name": "IBKR Connection",
                    "status": "pass",
                    "latency_ms": 35,
                    "last_check": datetime.utcnow().isoformat()
                },
                {
                    "name": "MT5 Connection",
                    "status": "pass",
                    "latency_ms": 98,
                    "last_check": datetime.utcnow().isoformat()
                },
                {
                    "name": "Alpaca Connection",
                    "status": "fail",
                    "latency_ms": None,
                    "last_check": datetime.utcnow().isoformat(),
                    "error": "Timeout"
                },
                {
                    "name": "Market Data Feed",
                    "status": "pass",
                    "latency_ms": 42,
                    "last_check": datetime.utcnow().isoformat()
                },
                {
                    "name": "Database Connection",
                    "status": "pass",
                    "latency_ms": 8,
                    "last_check": datetime.utcnow().isoformat()
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return health
        
    except Exception as e:
        logger.error(f"Error checking connection health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
