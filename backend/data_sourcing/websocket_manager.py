# backend/data_sourcing/websocket_manager.py

import asyncio
import logging
import json
import websockets
from typing import Dict, Any, List, Optional, Callable, Union, Awaitable, Set
from datetime import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from backend.config.settings import Settings

# Create settings instance
_settings = Settings()
from backend.data_sourcing.data_ingestion_framework import DataNormalizer

logger = logging.getLogger(__name__)

# --- Type Definitions ---
MessageHandler = Callable[[Dict[str, Any]], Awaitable[None]]

class ConnectionStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"

@dataclass
class WebSocketConfig:
    name: str
    url: str
    api_key: Optional[str] = None
    symbols: List[str] = field(default_factory=list)
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    ping_interval: int = 30
    ping_timeout: int = 10

class BaseWebSocketClient(ABC):
    """Abstract Base Class for WebSocket clients."""
    
    def __init__(self, config: WebSocketConfig, data_callback: MessageHandler):
        self.config = config
        self.data_callback = data_callback
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.status = ConnectionStatus.DISCONNECTED
        self.reconnect_attempts = 0
        self.is_running = False
        self.normalizer = DataNormalizer()
    
    async def start(self):
        """Public method to start the WebSocket client."""
        logger.info(f"Starting WebSocket client for {self.config.name}...")
        self.is_running = True
        await self._connect_with_retry()
    
    async def stop(self):
        """Public method to gracefully stop the WebSocket client."""
        logger.info(f"Stopping WebSocket client for {self.config.name}...")
        self.is_running = False
        if self.websocket and self.websocket.open:
            await self.websocket.close()
        self.status = ConnectionStatus.DISCONNECTED
    
    async def _connect_with_retry(self):
        """Manages the connection and reconnection loop."""
        while self.is_running:
            try:
                self.status = ConnectionStatus.CONNECTING
                logger.info(f"Connecting to {self.config.name} at {self.config.url}...")
                await self._connect()
                self.status = ConnectionStatus.CONNECTED
                logger.info(f"Successfully connected to {self.config.name}.")
                self.reconnect_attempts = 0
                await self._handle_messages()
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Connection closed for {self.config.name}. Attempting to reconnect.")
            except Exception as e:
                logger.error(f"WebSocket error for {self.config.name}: {e}", exc_info=True)
            
            if not self.is_running:
                break

            self.reconnect_attempts += 1
            if self.reconnect_attempts > self.config.max_reconnect_attempts:
                logger.error(f"Max reconnection attempts reached for {self.config.name}. Stopping.")
                self.status = ConnectionStatus.ERROR
                break
            
            self.status = ConnectionStatus.RECONNECTING
            logger.info(f"Reconnecting {self.config.name} in {self.config.reconnect_interval} seconds (attempt {self.reconnect_attempts})...")
            await asyncio.sleep(self.config.reconnect_interval)
    
    @abstractmethod
    async def _connect(self):
        """Provider-specific connection and authentication logic."""
        pass
    
    @abstractmethod
    async def _subscribe(self, symbols: List[str]):
        """Provider-specific subscription logic."""
        pass

    @abstractmethod
    async def _unsubscribe(self, symbols: List[str]):
        """Provider-specific unsubscription logic."""
        pass

    @abstractmethod
    def _parse_message(self, message: Union[str, bytes]) -> List[Dict[str, Any]]:
        """Provider-specific message parsing logic. Must return a list of messages."""
        pass
    
    async def _handle_messages(self):
        """Generic message handling loop."""
        async for message in self.websocket:
            if not self.is_running:
                break
            try:
                parsed_data_list = self._parse_message(message)
                for parsed_data in parsed_data_list:
                    if parsed_data:
                        normalized_data = self.normalizer.normalize_market_data(
                            parsed_data, self.config.name.lower()
                        )
                        normalized_data['websocket_source'] = self.config.name
                        await self.data_callback(normalized_data)
            except Exception as e:
                logger.error(f"Error processing message from {self.config.name}: {e}", exc_info=True)

    async def update_subscriptions(self, symbols_to_add: Set[str], symbols_to_remove: Set[str]):
        """Dynamically updates subscriptions for the client."""
        if symbols_to_add:
            await self._subscribe(list(symbols_to_add))
            self.config.symbols = list(set(self.config.symbols) | symbols_to_add)
        if symbols_to_remove:
            await self._unsubscribe(list(symbols_to_remove))
            self.config.symbols = list(set(self.config.symbols) - symbols_to_remove)

# --- Concrete Implementations ---

class FinnhubWebSocketClient(BaseWebSocketClient):
    async def _connect(self):
        if not self.config.api_key:
            raise ValueError("Finnhub API key is required.")
        url_with_token = f"{self.config.url}?token={self.config.api_key}"
        self.websocket = await websockets.connect(url_with_token)
        await self._subscribe(self.config.symbols)
    
    async def _subscribe(self, symbols: List[str]):
        for symbol in symbols:
            await self.websocket.send(json.dumps({"type": "subscribe", "symbol": symbol}))
            logger.info(f"Subscribed to {symbol} on Finnhub")

    async def _unsubscribe(self, symbols: List[str]):
        for symbol in symbols:
            await self.websocket.send(json.dumps({"type": "unsubscribe", "symbol": symbol}))
            logger.info(f"Unsubscribed from {symbol} on Finnhub")
    
    def _parse_message(self, message: str) -> List[Dict[str, Any]]:
        try:
            data = json.loads(message)
            if data.get("type") == "trade" and "data" in data:
                return data["data"] # Return the list of trades
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from Finnhub: {message}")
        return []

class PolygonWebSocketClient(BaseWebSocketClient):
    async def _connect(self):
        if not self.config.api_key:
            raise ValueError("Polygon API key is required.")
        
        self.websocket = await websockets.connect(self.config.url)
        
        auth_msg = {"action": "auth", "params": self.config.api_key}
        await self.websocket.send(json.dumps(auth_msg))
        
        auth_response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
        auth_data = json.loads(auth_response)
        
        if not (isinstance(auth_data, list) and auth_data[0].get("status") == "auth_success"):
            raise Exception(f"Polygon authentication failed: {auth_data}")
        
        await self._subscribe(self.config.symbols)

    async def _subscribe(self, symbols: List[str]):
        if not symbols: return
        params = ",".join([f"T.{s}" for s in symbols]) # Subscribe to Trades
        await self.websocket.send(json.dumps({"action": "subscribe", "params": params}))
        logger.info(f"Subscribed to trades for {len(symbols)} symbols on Polygon.")

    async def _unsubscribe(self, symbols: List[str]):
        if not symbols: return
        params = ",".join([f"T.{s}" for s in symbols])
        await self.websocket.send(json.dumps({"action": "unsubscribe", "params": params}))
        logger.info(f"Unsubscribed from trades for {len(symbols)} symbols on Polygon.")
    
    def _parse_message(self, message: str) -> List[Dict[str, Any]]:
        try:
            data = json.loads(message)
            if isinstance(data, list):
                # Filter for trade events 'T'
                return [item for item in data if item.get("ev") == "T"]
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from Polygon: {message}")
        return []

# --- Manager ---

class WebSocketManager:
    """Manages multiple WebSocket clients."""
    
    def __init__(self, data_handler=None):
        """
        Initialize WebSocketManager.
        
        Args:
            data_handler: Optional data handler for processing messages.
                         If None, messages will be logged but not processed.
        """
        self.handler = data_handler
        self.clients: Dict[str, BaseWebSocketClient] = {}
        self._tasks: List[asyncio.Task] = []
    
    async def _default_handler(self, data: Dict[str, Any]):
        """Default handler when no data handler is provided."""
        logger.info(f"WebSocket data received (no handler): {data}")

    def initialize_clients(self, initial_subscriptions: Dict[str, List[str]]):
        """Initializes clients based on configured API keys and symbols."""
        logger.info("Initializing WebSocket clients from configuration...")

        if _settings.FINNHUB_API_KEY and "Finnhub" in initial_subscriptions:
            config = WebSocketConfig(name="Finnhub", url="wss://ws.finnhub.io", api_key=_settings.FINNHUB_API_KEY, symbols=initial_subscriptions["Finnhub"])
            callback = self.handler.handle_data if self.handler else self._default_handler
            self.clients["Finnhub"] = FinnhubWebSocketClient(config, callback)
            logger.info("Finnhub WebSocket client configured.")

        if _settings.POLYGON_API_KEY and "Polygon" in initial_subscriptions:
            config = WebSocketConfig(name="Polygon", url="wss://socket.polygon.io/stocks", api_key=_settings.POLYGON_API_KEY, symbols=initial_subscriptions["Polygon"])
            callback = self.handler.handle_data if self.handler else self._default_handler
            self.clients["Polygon"] = PolygonWebSocketClient(config, callback)
            logger.info("Polygon WebSocket client configured.")
            
        # Add Binance or other clients here similarly

    async def start_all(self):
        """Starts all configured WebSocket clients."""
        if not self.clients:
            logger.warning("No WebSocket clients configured to start.")
            return
        logger.info(f"Starting {len(self.clients)} WebSocket client(s)...")
        for client in self.clients.values():
            task = asyncio.create_task(client.start())
            self._tasks.append(task)

    async def stop_all(self):
        """Stops all running WebSocket clients."""
        logger.info("Stopping all WebSocket clients...")
        for client in self.clients.values():
            await client.stop()
        for task in self._tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("All WebSocket clients stopped.")

    async def update_subscriptions(self, provider: str, symbols_to_add: List[str] = None, symbols_to_remove: List[str] = None):
        """Adds or removes subscriptions from a running client."""
        client = self.clients.get(provider)
        if client:
            await client.update_subscriptions(set(symbols_to_add or []), set(symbols_to_remove or []))
        else:
            logger.error(f"Cannot update subscriptions, provider '{provider}' not found.")

