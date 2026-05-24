# backend/trading_engine/broker_gateway.py
"""
Broker Gateway Service
Routes requests to isolated broker microservices to avoid dependency conflicts.
"""

import logging
import httpx
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class BrokerServiceType(str, Enum):
    """Broker service types"""
    INTERACTIVE_BROKERS = "ib"
    ALPACA = "alpaca"
    BINANCE = "binance"
    DERIV = "deriv"
    MT5 = "mt5"


class BrokerGateway:
    """
    Gateway to route broker requests to isolated microservices.
    
    This allows each broker to run in its own container with its own
    dependencies, avoiding conflicts like Pydantic v1 vs v2.
    """
    
    # Service URLs (can be configured via environment variables)
    SERVICE_URLS = {
        BrokerServiceType.INTERACTIVE_BROKERS: "http://ib-service:8085",
        BrokerServiceType.ALPACA: "http://alpaca-service:8083",
        BrokerServiceType.BINANCE: "http://binance-service:8084",
        BrokerServiceType.DERIV: "http://deriv-service:8086",
        BrokerServiceType.MT5: "http://mt5-service:8087",
    }
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.connections: Dict[str, BrokerServiceType] = {}
        logger.info("BrokerGateway initialized")
    
    def _get_service_url(self, broker_type: BrokerServiceType) -> str:
        """Get the service URL for a broker type"""
        return self.SERVICE_URLS.get(broker_type)
    
    async def connect_broker(
        self,
        broker_id: str,
        broker_type: BrokerServiceType,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Connect to a broker via its microservice.
        
        Args:
            broker_id: Unique identifier for this connection
            broker_type: Type of broker
            config: Broker-specific configuration
        
        Returns:
            Connection result
        """
        try:
            service_url = self._get_service_url(broker_type)
            if not service_url:
                raise ValueError(f"Unknown broker type: {broker_type}")
            
            # Send connect request to microservice
            response = await self.client.post(
                f"{service_url}/connect",
                json=config
            )
            response.raise_for_status()
            
            # Store connection
            self.connections[broker_id] = broker_type
            
            result = response.json()
            logger.info(f"Connected to {broker_type} broker: {broker_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to connect to {broker_type}: {e}")
            raise
    
    async def disconnect_broker(self, broker_id: str) -> Dict[str, Any]:
        """Disconnect from a broker"""
        try:
            if broker_id not in self.connections:
                raise ValueError(f"Broker {broker_id} not connected")
            
            broker_type = self.connections[broker_id]
            service_url = self._get_service_url(broker_type)
            
            response = await self.client.post(f"{service_url}/disconnect")
            response.raise_for_status()
            
            del self.connections[broker_id]
            
            logger.info(f"Disconnected from broker: {broker_id}")
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to disconnect from {broker_id}: {e}")
            raise
    
    async def get_account_info(self, broker_id: str) -> Dict[str, Any]:
        """Get account information from a broker"""
        try:
            if broker_id not in self.connections:
                raise ValueError(f"Broker {broker_id} not connected")
            
            broker_type = self.connections[broker_id]
            service_url = self._get_service_url(broker_type)
            
            response = await self.client.get(f"{service_url}/account")
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get account info from {broker_id}: {e}")
            raise
    
    async def get_positions(self, broker_id: str) -> Dict[str, Any]:
        """Get open positions from a broker"""
        try:
            if broker_id not in self.connections:
                raise ValueError(f"Broker {broker_id} not connected")
            
            broker_type = self.connections[broker_id]
            service_url = self._get_service_url(broker_type)
            
            response = await self.client.get(f"{service_url}/positions")
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get positions from {broker_id}: {e}")
            raise
    
    async def execute_trade(
        self,
        broker_id: str,
        trade_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a trade via a broker"""
        try:
            if broker_id not in self.connections:
                raise ValueError(f"Broker {broker_id} not connected")
            
            broker_type = self.connections[broker_id]
            service_url = self._get_service_url(broker_type)
            
            response = await self.client.post(
                f"{service_url}/trade",
                json=trade_params
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to execute trade on {broker_id}: {e}")
            raise
    
    async def health_check(self, broker_type: BrokerServiceType) -> Dict[str, Any]:
        """Check health of a broker service"""
        try:
            service_url = self._get_service_url(broker_type)
            response = await self.client.get(f"{service_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed for {broker_type}: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def close(self):
        """Close the gateway and all connections"""
        await self.client.aclose()


# Global gateway instance
broker_gateway = BrokerGateway()

