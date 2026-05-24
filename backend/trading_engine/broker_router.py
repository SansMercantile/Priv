# backend/trading_engine/broker_router.py

import logging
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
import time

# Import the interface from its dedicated file
from .broker_interface import BaseTradeAPIAdapter

logger = logging.getLogger(__name__)

class BrokerRouter:
    """
    Manages multiple trading API adapters and intelligently routes trade requests.
    It performs health checks and selects the best available adapter.
    """
    def __init__(self, adapters: Optional[List[BaseTradeAPIAdapter]] = None):
        self.adapters: List[BaseTradeAPIAdapter] = adapters if adapters is not None else []
        self.adapter_health: Dict[str, Dict[str, Any]] = {}
        self.last_health_check: Optional[datetime] = None
        self._health_check_interval_seconds = 60
        logger.info(f"Priv BrokerRouter initialized with {len(self.adapters)} adapters.")

    def add_adapter(self, adapter: BaseTradeAPIAdapter):
        """Adds a new trading adapter to the router."""
        if adapter not in self.adapters:
            self.adapters.append(adapter)
            logger.info(f"Priv BrokerRouter: Added adapter: {adapter.name}")

    async def _perform_health_check(self, adapter: BaseTradeAPIAdapter):
        """Performs a health check on a single adapter."""
        start_time = time.monotonic()
        is_healthy = False
        try:
            if not adapter.is_connected:
                await adapter.connect()
            
            if adapter.is_connected:
                info = await adapter.get_account_info()
                if info:
                    is_healthy = True
        except Exception as e:
            logger.warning(f"Priv BrokerRouter: Health check failed for {adapter.name}: {e}", exc_info=False)
            is_healthy = False
        finally:
            latency = (time.monotonic() - start_time) * 1000
            self.adapter_health[adapter.name] = {
                "is_healthy": is_healthy,
                "latency_ms": latency,
                "last_checked": datetime.now().isoformat()
            }
            logger.debug(f"Health check for {adapter.name}: Healthy={is_healthy}, Latency={latency:.2f}ms")

    async def refresh_all_adapter_health(self):
        """Refreshes the health status of all registered adapters."""
        tasks = [self._perform_health_check(adapter) for adapter in self.adapters]
        await asyncio.gather(*tasks)
        self.last_health_check = datetime.now()
        logger.info("Priv BrokerRouter: All adapter health statuses refreshed.")

    async def select_adapter(self, criteria: Dict[str, Any] = None) -> Optional[BaseTradeAPIAdapter]:
        """Selects the best available adapter based on health and optional criteria."""
        if self.last_health_check is None or \
           (datetime.now() - self.last_health_check).total_seconds() > self._health_check_interval_seconds:
            await self.refresh_all_adapter_health()

        healthy_adapters = [
            adapter for adapter in self.adapters
            if self.adapter_health.get(adapter.name, {}).get("is_healthy")
        ]

        if not healthy_adapters:
            logger.error("Priv BrokerRouter: No healthy adapters available.")
            return None
        
        best_adapter = min(healthy_adapters, key=lambda adp: self.adapter_health.get(adp.name, {}).get("latency_ms", float('inf')))
        
        if best_adapter:
            latency = self.adapter_health.get(best_adapter.name, {}).get('latency_ms', 0)
            logger.debug(f"Priv BrokerRouter: Selected adapter: {best_adapter.name} (Latency: {latency:.2f}ms)")
        
        return best_adapter

# --- CREATE THE GLOBAL INSTANCE ---
# This single instance will be configured and used by the rest of the application.
broker_router = BrokerRouter()