# backend/multi_agent/priv_arbitrage_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeAction, TradeProposal, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

# Import actual data sourcing clients
from backend.data_sourcing.market_data_ingestor import MarketDataIngestor
from backend.data_sourcing.cross_rate_calculator import get_synthetic_cross_rates # For synthetic pairs

# Import settings for configurable thresholds
from backend.config import settings

logger = logging.getLogger(__name__)

class PrivArbitrageAgent(PrivAgent):
    """
    A specialized Priv Agent focused on identifying and exploiting arbitrage opportunities
    across different exchanges or instruments, using real-time market data.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.ARBITRAGE, message_broker=message_broker, broker=broker, persona=persona)
        self.message_broker = message_broker
        self.is_running = False
        self.last_arbitrage_opportunity: Dict[str, Any] = {"symbol": None, "profit_pct": 0.0, "time": None}
        
        # Store latest market data, indexed by symbol and then by source
        # {"SYMBOL": {"SOURCE_A": {"price": X, "timestamp": Y}, "SOURCE_B": {"price": Z, ...}}}
        self.latest_market_data_by_source: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Initialize MarketDataIngestor to potentially fetch data if not received via broker
        self.market_data_ingestor = MarketDataIngestor(self.broker)

        logger.info(f"Priv Arbitrage Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the arbitrage agent, subscribing to real-time market data."""
        if self.is_running:
            logger.warning(f"Arbitrage Agent '{self.agent_id}' is already running.")
            return
        
        # Subscribe to real-time market data from the ingestor
        await self.broker.subscribe_to_topic(
            "real_time_market_data", self._handle_real_time_market_data, f"{self.agent_id}-market-data-sub"
        )

        self.is_running = True
        # Start a periodic task to scan for opportunities across all tracked symbols
        self._periodic_arbitrage_scan_task = asyncio.create_task(self._periodic_arbitrage_scan())
        logger.info(f"Priv Arbitrage Agent '{self.agent_id}' started and subscribed to 'real_time_market_data'.")

    async def stop(self):
        """Stops the arbitrage agent."""
        if not self.is_running:
            logger.warning(f"Arbitrage Agent '{self.agent_id}' is not running.")
            return
        
        self.is_running = False
        if self._periodic_arbitrage_scan_task:
            self._periodic_arbitrage_scan_task.cancel()
            try:
                await self._periodic_arbitrage_scan_task
            except asyncio.CancelledError:
                logger.info(f"Priv Arbitrage Agent '{self.agent_id}' periodic scan task cancelled.")

        logger.info(f"Priv Arbitrage Agent '{self.agent_id}' stopped.")

    async def _periodic_arbitrage_scan(self):
        """
        Periodically triggers an arbitrage scan for all currently tracked symbols.
        This ensures opportunities are not missed if data arrives asynchronously.
        """
        while self.is_running:
            try:
                logger.info(f"Priv Arbitrage Agent '{self.agent_id}': Initiating periodic arbitrage scan.")
                symbols_to_scan = list(self.latest_market_data_by_source.keys())
                for symbol in symbols_to_scan:
                    proposal = await self.scan_for_arbitrage_opportunity(symbol)
                    if proposal:
                        logger.info(f"Arbitrage Agent: Found and published proposal for {symbol}.")
                        # Break after finding one to prioritize fast execution, or continue for all
                        break # Only act on the first one found per scan cycle
            except Exception as e:
                logger.error(f"Priv Arbitrage Agent '{self.agent_id}': Error during periodic arbitrage scan: {e}", exc_info=True)
            
            await asyncio.sleep(settings.ARBITRAGE_SCAN_INTERVAL_SECONDS) # Configurable interval

    async def _handle_real_time_market_data(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming real-time market data messages.
        Stores prices by symbol and source. Triggers immediate scan if configured.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            market_data_item = agent_message.payload # Assuming payload is the market data dict

            symbol = market_data_item.get("symbol")
            source = market_data_item.get("source")
            bid_price = market_data_item.get("bid_price")
            ask_price = market_data_item.get("ask_price")

            # Ensure bid/ask are present for arbitrage calculation
            if not all([symbol, source, bid_price is not None, ask_price is not None]):
                logger.warning(f"Arbitrage Agent: Received incomplete market data (missing bid/ask): {market_data_item}. Skipping.")
                return

            if symbol not in self.latest_market_data_by_source:
                self.latest_market_data_by_source[symbol] = {}
            
            self.latest_market_data_by_source[symbol][source] = {
                "bid_price": bid_price,
                "ask_price": ask_price,
                "timestamp": market_data_item.get("timestamp") # Keep original timestamp
            }
            logger.debug(f"Arbitrage Agent '{self.agent_id}' updated live data for {symbol} from {source}: Bid: {bid_price}, Ask: {ask_price}.")

            # Trigger arbitrage scan immediately after receiving an update for a critical symbol
            if symbol in settings.ARBITRAGE_CRITICAL_SYMBOLS:
                await self.scan_for_arbitrage_opportunity(symbol)

        except Exception as e:
            logger.error(f"Arbitrage Agent '{self.agent_id}': Error processing real-time market data message: {e}", exc_info=True)

    async def scan_for_arbitrage_opportunity(self, symbol: str) -> Optional[TradeProposal]:
        """
        Scans for arbitrage opportunities for a given symbol using the internally stored prices.
        This method is now called *without* direct market_data arguments.
        """
        logger.info(f"Arbitrage Agent '{self.agent_id}' scanning for arbitrage on {symbol}...")

        # Get prices from different sources for the same symbol
        sources_data = self.latest_market_data_by_source.get(symbol)
        if not sources_data or len(sources_data) < 2:
            logger.debug(f"Arbitrage Agent: Not enough data sources ({len(sources_data) if sources_data else 0}) for {symbol} to scan for arbitrage.")
            return None

        # Prepare data for synthetic cross-rate calculation if it's a cross pair
        # This assumes all_symbol_prices includes all necessary legs for the cross
        all_current_prices_flat = {}
        for sym, data_by_source in self.latest_market_data_by_source.items():
            # Use the latest price from any source for the flat map
            if data_by_source:
                latest_source_data = list(data_by_source.values())[0] # Just take the first available
                all_current_prices_flat[sym] = {
                    "bid": latest_source_data.get("bid_price"),
                    "ask": latest_source_data.get("ask_price")
                }
        
        # Check if the symbol itself is a cross-pair that can be synthesized
        synthetic_rates = get_synthetic_cross_rates(symbol, all_current_prices_flat)
        if synthetic_rates:
            # Add synthetic rates as a "source" for arbitrage calculation
            sources_data["_SYNTHETIC_"] = {
                "bid_price": synthetic_rates["synthetic_bid"],
                "ask_price": synthetic_rates["synthetic_ask"],
                "timestamp": datetime.now().isoformat()
            }
            logger.debug(f"Arbitrage Agent: Added synthetic rates for {symbol}.")


        best_buy_price = float('inf')
        best_buy_source = None
        best_sell_price = 0.0
        best_sell_source = None

        for source_name, data in sources_data.items():
            if data.get("ask_price") is not None:
                if data["ask_price"] < best_buy_price:
                    best_buy_price = data["ask_price"]
                    best_buy_source = source_name
            
            if data.get("bid_price") is not None:
                if data["bid_price"] > best_sell_price:
                    best_sell_price = data["bid_price"]
                    best_sell_source = source_name

        if best_buy_source and best_sell_source and best_buy_source != best_sell_source:
            # Calculate potential profit
            price_difference = best_sell_price - best_buy_price
            profit_percentage = (price_difference / best_buy_price) * 100 if best_buy_price != 0 else 0

            arbitrage_threshold_pct = settings.ARBITRAGE_PROFIT_THRESHOLD_PCT # Minimum profit to consider (adjust for fees)

            if profit_percentage > arbitrage_threshold_pct:
                action = TradeAction.BUY # Buy from best_buy_source, Sell to best_sell_source
                confidence = settings.ARBITRAGE_CONFIDENCE_SCORE # High confidence for detected arbitrage
                reasoning = (f"Arbitrage opportunity: Buy {symbol} on {best_buy_source} ({best_buy_price:.5f}) "
                             f"and Sell on {best_sell_source} ({best_sell_price:.5f}). "
                             f"Potential Profit: {profit_percentage:.4f}%." )
                volume = settings.ARBITRAGE_TRADE_VOLUME # Configurable volume for arbitrage

                self.last_arbitrage_opportunity = {
                    "symbol": symbol,
                    "profit_pct": profit_percentage,
                    "time": datetime.now().isoformat(),
                    "action": action.value,
                    "buy_source": best_buy_source,
                    "sell_source": best_sell_source
                }

                prop = TradeProposal(
                    agent_id=self.agent_id,
                    symbol=symbol,
                    action=action,
                    volume=volume,
                    entry_price=best_buy_price, # Conceptual entry price for the buy leg
                    reasoning=reasoning,
                    confidence=confidence,
                    risk_assessment={"arbitrage_risk": "low_latency", "execution_complexity": "high", "profit_pct": profit_percentage}
                )
                logger.info(f"Arbitrage Agent '{self.agent_id}' generated proposal: {prop.action} {prop.symbol} (Profit: {profit_percentage:.2f}%) with confidence {prop.confidence:.2f}.")
                
                # Publish the proposal to the trade_proposals topic
                await self.broker.publish_message("trade_proposals", prop.model_dump())
                return prop
        
        logger.debug(f"Arbitrage Agent: No profitable arbitrage opportunity found for {symbol} above threshold {arbitrage_threshold_pct:.2f}%.")
        return None

    async def generate_trade_proposal(self, symbols_to_scan: Optional[List[str]] = None) -> Optional[TradeProposal]:
        """
        Triggers an arbitrage scan for specified symbols or all currently tracked symbols.
        Returns the *first* profitable proposal found.
        """
        if symbols_to_scan is None:
            symbols_to_scan = list(self.latest_market_data_by_source.keys())
        
        for symbol in symbols_to_scan:
            proposal = await self.scan_for_arbitrage_opportunity(symbol)
            if proposal:
                return proposal # Return the first profitable one found
        
        logger.info("Arbitrage Agent: No new profitable arbitrage proposals generated during this scan.")
        return None


# Example Usage (for testing PrivArbitrageAgent in isolation)
async def main_arbitrage_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType # Import AgentMessage, MessageType

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    # Set dummy values for settings if not already present for local testing
    if not hasattr(settings, 'ARBITRAGE_SCAN_INTERVAL_SECONDS'):
        settings.ARBITRAGE_SCAN_INTERVAL_SECONDS = 5 # Scan every 5 seconds for test
    if not hasattr(settings, 'ARBITRAGE_CRITICAL_SYMBOLS'):
        settings.ARBITRAGE_CRITICAL_SYMBOLS = ["ETHUSD", "BTCUSD"]
    if not hasattr(settings, 'ARBITRAGE_PROFIT_THRESHOLD_PCT'):
        settings.ARBITRAGE_PROFIT_THRESHOLD_PCT = 0.05 # 0.05% profit
    if not hasattr(settings, 'ARBITRAGE_CONFIDENCE_SCORE'):
        settings.ARBITRAGE_CONFIDENCE_SCORE = 0.99
    if not hasattr(settings, 'ARBITRAGE_TRADE_VOLUME'):
        settings.ARBITRAGE_TRADE_VOLUME = 0.1


    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    arbitrage_agent = PrivArbitrageAgent(
        agent_id="Priv-Arbitrage",
        broker=broker,
        persona={"name": "Arbitrageur", "focus": "Price Discrepancies", "role": "arbitrageur"}
    )

    await broker.connect()
    await arbitrage_agent.start()

    # Simulate real-time market data from different sources for the same symbols
    mock_eth_polygon = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={"symbol": "ETHUSD", "bid_price": 2000.00, "ask_price": 2000.10, "last_trade_price": 2000.05, "timestamp": datetime.now().timestamp() * 1e9, "source": "Polygon.io", "type": "market_data_quote"}
    )
    mock_eth_finnhub = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={"symbol": "ETHUSD", "bid_price": 2001.50, "ask_price": 2001.60, "last_trade_price": 2001.55, "timestamp": (datetime.now() + timedelta(seconds=0.1)).timestamp() * 1e9, "source": "Finnhub.io", "type": "market_data_quote"}
    ) # This creates an arbitrage opportunity (Buy Polygon, Sell Finnhub)

    mock_btc_twelvedata = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={"symbol": "BTCUSD", "bid_price": 30000.00, "ask_price": 30000.10, "last_trade_price": 30000.05, "timestamp": datetime.now().timestamp() * 1e9, "source": "TwelveData.com", "type": "market_data_quote"}
    )
    mock_btc_polygon = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={"symbol": "BTCUSD", "bid_price": 29990.00, "ask_price": 29990.10, "last_trade_price": 29990.05, "timestamp": (datetime.now() + timedelta(seconds=0.1)).timestamp() * 1e9, "source": "Polygon.io", "type": "market_data_quote"}
    ) # This creates an arbitrage opportunity (Buy Polygon, Sell TwelveData)

    mock_xrp_no_arbitrage_source_a = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={"symbol": "XRPUSD", "bid_price": 0.5000, "ask_price": 0.5001, "last_trade_price": 0.50005, "timestamp": datetime.now().timestamp() * 1e9, "source": "Polygon.io", "type": "market_data_quote"}
    )
    mock_xrp_no_arbitrage_source_b = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={"symbol": "XRPUSD", "bid_price": 0.5001, "ask_price": 0.5002, "last_trade_price": 0.50015, "timestamp": (datetime.now() + timedelta(seconds=0.1)).timestamp() * 1e9, "source": "Finnhub.io", "type": "market_data_quote"}
    ) # No significant arbitrage opportunity

    # Simulate prices for cross-rate calculation (e.g., EURUSD and GBPUSD for EURGBP)
    mock_eurusd_price = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={"symbol": "EURUSD", "bid_price": 1.0850, "ask_price": 1.0855, "last_trade_price": 1.0852, "timestamp": datetime.now().timestamp() * 1e9, "source": "Polygon.io", "type": "market_data_quote"}
    )
    mock_gbpusd_price = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={"symbol": "GBPUSD", "bid_price": 1.2700, "ask_price": 1.2705, "last_trade_price": 1.2702, "timestamp": datetime.now().timestamp() * 1e9, "source": "Finnhub.io", "type": "market_data_quote"}
    )

    logger.info("\n--- Simulating real-time market data arrival for Arbitrage Agent ---")
    await broker.publish_message("real_time_market_data", mock_eth_polygon.model_dump())
    await asyncio.sleep(0.1)
    await broker.publish_message("real_time_market_data", mock_eth_finnhub.model_dump())
    await asyncio.sleep(0.5)

    await broker.publish_message("real_time_market_data", mock_btc_twelvedata.model_dump())
    await asyncio.sleep(0.1)
    await broker.publish_message("real_time_market_data", mock_btc_polygon.model_dump())
    await asyncio.sleep(0.5)

    await broker.publish_message("real_time_market_data", mock_xrp_no_arbitrage_source_a.model_dump())
    await asyncio.sleep(0.1)
    await broker.publish_message("real_time_market_data", mock_xrp_no_arbitrage_source_b.model_dump())
    await asyncio.sleep(0.5)

    await broker.publish_message("real_time_market_data", mock_eurusd_price.model_dump())
    await asyncio.sleep(0.1)
    await broker.publish_message("real_time_market_data", mock_gbpusd_price.model_dump())
    await asyncio.sleep(1) # Give agent time to process all incoming data

    logger.info("\n--- Arbitrage Agent triggering arbitrage scan using internal data ---")
    prop1 = await arbitrage_agent.generate_trade_proposal(symbols_to_scan=["ETHUSD"])
    if prop1:
        logger.info(f"Arbitrage Proposal 1 (ETHUSD): {prop1.action} {prop1.symbol} (Confidence: {prop1.confidence:.2f})")
    else:
        logger.info("Arbitrage Agent: No ETHUSD proposal found.")

    prop2 = await arbitrage_agent.generate_trade_proposal(symbols_to_scan=["BTCUSD"])
    if prop2:
        logger.info(f"Arbitrage Proposal 2 (BTCUSD): {prop2.action} {prop2.symbol} (Confidence: {prop2.confidence:.2f})")
    else:
        logger.info("Arbitrage Agent: No BTCUSD proposal found.")
    
    prop3 = await arbitrage_agent.generate_trade_proposal(symbols_to_scan=["XRPUSD"])
    if prop3:
        logger.info(f"Arbitrage Proposal 3 (XRPUSD): {prop3.action} {prop3.symbol} (Confidence: {prop3.confidence:.2f})")
    else:
        logger.info("Arbitrage Agent: No XRPUSD proposal found (expected).")

    # Test synthetic arbitrage (EURGBP)
    logger.info("\n--- Arbitrage Agent triggering synthetic arbitrage scan for EURGBP ---")
    prop_eurgbp = await arbitrage_agent.scan_for_arbitrage_opportunity("EURGBP")
    if prop_eurgbp:
        logger.info(f"Arbitrage Proposal (EURGBP Synthetic): {prop_eurgbp.action} {prop_eurgbp.symbol} (Confidence: {prop_eurgbp.confidence:.2f})")
    else:
        logger.info("Arbitrage Agent: No synthetic EURGBP proposal found.")


    await asyncio.sleep(5) # Give time for periodic scan to run
    await arbitrage_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivArbitrageAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_arbitrage_agent_test())
