"""
System API endpoints for PRIV backend.
Provides system health, status, and configuration information.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import logging
import psutil
import platform

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """
    Get system health status.
    """
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Determine health status
        status = "healthy"
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
            status = "degraded"
        
        return {
            "success": True,
            "data": {
                "status": status,
                "uptime_seconds": 3600,  # Mock uptime
                "services": {
                    "api": "operational",
                    "database": "operational",
                    "cache": "operational",
                    "background_tasks": "operational"
                },
                "system_metrics": {
                    "cpu_usage_pct": cpu_percent,
                    "memory_usage_pct": memory.percent,
                    "memory_available_mb": memory.available / (1024 * 1024),
                    "disk_usage_pct": disk.percent,
                    "disk_free_gb": disk.free / (1024 ** 3)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error fetching system health: {e}")
        return {
            "success": False,
            "data": {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        }


@router.get("/info")
async def get_system_info() -> Dict[str, Any]:
    """
    Get system information.
    """
    try:
        return {
            "success": True,
            "data": {
                "app_name": "Sans Mercantile PRIV AI",
                "version": "2.0.0",
                "environment": "development",
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version()
                },
                "features": {
                    "multi_agent_system": True,
                    "real_time_data": True,
                    "risk_analysis": True,
                    "news_sentiment": True,
                    "portfolio_management": True
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error fetching system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """
    Get detailed system status.
    """
    try:
        return {
            "success": True,
            "data": {
                "api_server": {
                    "status": "running",
                    "port": 8000,
                    "workers": 1
                },
                "background_tasks": {
                    "news_scraper": "active",
                    "market_data_polling": "active",
                    "broker_monitoring": "active"
                },
                "integrations": {
                    "openai": "connected",
                    "firebase": "connected",
                    "redis": "disconnected",
                    "postgresql": "disconnected"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error fetching system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
