"""
Connections API endpoints for PRIV backend.
Provides broker connection status and management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import logging
import os
import json

from ..trading_engine.broker_api import broker_manager

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

    Sourced from the real broker_manager singleton (registered adapters, e.g.
    priv_deriv), plus any broker credentials the user has saved locally via
    /save-broker-keys. Previously this returned four fully hardcoded brokers
    (IBKR, MT5, Alpaca, Polygon.io) that were never actually connected.
    """
    try:
        connections: List[Dict[str, Any]] = []

        statuses = await broker_manager.get_all_brokers_status()
        for status in statuses:
            broker_id = status.get("broker_id")
            connected = bool(status.get("connected", False))
            entry: Dict[str, Any] = {
                "id": broker_id,
                "name": status.get("adapter_name", broker_id),
                "status": "connected" if connected else "disconnected",
            }
            if connected:
                try:
                    account = await broker_manager.get_account_info(broker_id)
                except Exception as exc:
                    logger.warning(f"Could not fetch account info for {broker_id}: {exc}")
                    account = {}
                if account and "error" not in account:
                    entry["account_id"] = account.get("account_id")
                    entry["currency"] = account.get("currency")
            connections.append(entry)

        saved_connections = _load_saved_connections()
        known_names = {c.get("name") for c in connections}
        for saved in saved_connections:
            if saved.get("broker_name") in known_names:
                continue
            connections.append({
                "id": saved.get("id"),
                "name": saved.get("broker_name"),
                "status": saved.get("status", "connected"),
                "account_id": saved.get("api_key_masked"),
                "saved_at": saved.get("saved_at"),
            })

        total = len(connections)
        connected_count = sum(1 for c in connections if c["status"] == "connected")

        return {
            "connections": connections,
            "summary": {
                "total": total,
                "connected": connected_count,
                "disconnected": total - connected_count,
                "health_score": round((connected_count / total) * 100, 1) if total else 0.0,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error fetching broker connections: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brokers/{broker_id}")
async def get_broker_details(broker_id: str) -> Dict[str, Any]:
    """
    Get detailed information for a specific broker connection.

    Args:
        broker_id: ID of the broker connection (e.g. "priv_deriv")

    Returns:
        Real status + account info from broker_manager. Previously this
        endpoint ignored broker_id entirely and returned hardcoded fake
        Interactive Brokers connection history and config.
    """
    try:
        status = await broker_manager.get_broker_status(broker_id)
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])

        account: Dict[str, Any] = {}
        if status.get("connected"):
            try:
                account = await broker_manager.get_account_info(broker_id)
            except Exception as exc:
                logger.warning(f"Could not fetch account info for {broker_id}: {exc}")

        return {
            "id": broker_id,
            "name": status.get("adapter_name", broker_id),
            "status": "connected" if status.get("connected") else "disconnected",
            "account": account if account and "error" not in account else None,
            "note": "Per-connection uptime/latency history is not yet persisted by the backend.",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching broker details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_connection_health() -> Dict[str, Any]:
    """
    Get overall connection health status, derived from real registered brokers.

    Previously this returned five hardcoded checks (IBKR/MT5/Alpaca/market
    data/database) with fixed fake latency numbers regardless of what was
    actually registered.
    """
    try:
        statuses = await broker_manager.get_all_brokers_status()
        checks = [
            {
                "name": s.get("adapter_name", s.get("broker_id")),
                "status": "pass" if s.get("connected") else "fail",
                "last_check": datetime.utcnow().isoformat(),
            }
            for s in statuses
        ]
        total = len(checks)
        passing = sum(1 for c in checks if c["status"] == "pass")
        health_score = round((passing / total) * 100, 1) if total else 0.0

        return {
            "overall_status": "healthy" if total and passing == total else ("degraded" if passing else "unhealthy"),
            "health_score": health_score,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error checking connection health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
