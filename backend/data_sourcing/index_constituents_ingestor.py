# backend/data_sourcing/index_constituents_ingestor.py

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx
from backend.config.settings import Settings

# Create settings instance
_settings = Settings()
from backend.multi_agent.priv_agent_protocol import MessageType

logger = logging.getLogger(__name__)

class IndexConstituentsIngestor:
    """
    Ingests index constituents data for major stock indices.
    Handles data fetching, validation, and publishing with robust error handling.
    """
    
    def __init__(self):
        self.session = None
        self.message_broker = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={"User-Agent": "PRIV-IndexConstituentsIngestor/1.0"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    async def connect(self, message_broker=None):
        """Connect to message broker for data publishing."""
        self.message_broker = message_broker
        logger.info("IndexConstituentsIngestor connected to message broker")
        
    async def fetch_index_constituents(self, index_symbol: str) -> List[Dict[str, Any]]:
        """
        Fetch constituents for a specific index.
        
        Args:
            index_symbol: Index symbol (e.g., 'SPY', 'QQQ', 'DIA')
            
        Returns:
            List of constituent dictionaries with symbol, name, weight, etc.
        """
        logger.info(f"Fetching constituents for index: {index_symbol}")
        
        # This is a placeholder implementation
        # In a real scenario, you would fetch from actual index providers
        mock_constituents = [
            {"symbol": "AAPL", "name": "Apple Inc.", "weight": 6.5},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "weight": 5.8},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "weight": 4.2},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "weight": 3.9},
            {"symbol": "TSLA", "name": "Tesla Inc.", "weight": 3.5},
        ]
        
        logger.info(f"Successfully fetched {len(mock_constituents)} constituents for {index_symbol}")
        return mock_constituents
    
    async def fetch_and_publish_constituents(self, indices: List[str], broker_instance: Any):
        """
        Fetch constituents for multiple indices and publish to message broker.
        
        Args:
            indices: List of index symbols
            broker_instance: Message broker instance for publishing
        """
        logger.info(f"Fetching and publishing constituents for indices: {indices}")
        
        for index in indices:
            try:
                constituents = await self.fetch_index_constituents(index)
                
                if constituents:
                    agent_message = {
                        "sender_id": "IndexConstituentsIngestor",
                        "message_type": MessageType.STATUS_UPDATE,
                        "payload": {
                            "index": index,
                            "constituents": constituents,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    await broker_instance.publish_message("index_constituents_updates", agent_message)
                    logger.debug(f"Published constituents for {index}")
                else:
                    logger.warning(f"No constituents found for {index}")
                    
            except Exception as e:
                logger.error(f"Error fetching constituents for {index}: {e}")
                
            await asyncio.sleep(0.5)  # Rate limiting

# Example Usage (for testing IndexConstituentsIngestor in isolation)
async def main_index_constituents_ingestor_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config.settings import Settings

    # Create settings instance
    _settings = Settings()
    
    project_id = _settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    await broker.connect()

    ingestor = IndexConstituentsIngestor()
    
    test_indices = ["SPY", "QQQ", "DIA"]  # Example indices
    
    print("\n--- Testing IndexConstituentsIngestor fetching and publishing ---")
    await ingestor.fetch_and_publish_constituents(test_indices, broker)

    await asyncio.sleep(5)
    await broker.disconnect()
    print("\nIndexConstituentsIngestor test finished.")

if __name__ == '__main__':
    asyncio.run(main_index_constituents_ingestor_test())