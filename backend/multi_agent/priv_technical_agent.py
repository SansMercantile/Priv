# backend/multi_agent/priv_technical_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd # Import pandas for data manipulation

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeAction, TradeProposal, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

# Import actual data sourcing clients
from backend.data_sourcing.market_data_ingestor import MarketDataIngestor
from backend.data_sourcing.data_loader import get_market_data # For historical OHLCV data

# Import settings for configurable thresholds
from backend.config import settings

# Import the actual technical analysis engine
from backend.support_ai.analytics_engine import AnalyticsEngine

# MATLAB integration for advanced technical analysis
from backend.utils.matlab_integration import get_matlab_engine


logger = logging.getLogger(__name__)

class PrivTechnicalAgent(PrivAgent):
    async def analyze_technical_indicators(self, market_data):
        """Stub for technical indicator analysis"""
        return {
            'rsi': 50,
            'macd': {'value': 0},
            'bollinger_bands': {'upper': 100, 'lower': 90},
            'moving_averages': [100, 105]
        }

    async def recognize_patterns(self, market_data):
        """Stub for pattern recognition"""
        return [{'pattern_type': 'head_and_shoulders', 'confidence': 0.8, 'start_index': 0, 'end_index': 10}]

    async def identify_support_resistance(self, market_data):
        """Stub for support/resistance identification"""
        return {
            'support_levels': [{'price': 95, 'strength': 0.7}],
            'resistance_levels': [{'price': 110, 'strength': 0.6}]
        }
    """
    A specialized Priv Agent focused on technical analysis and past market behavior.
    This agent will generate trade proposals based on technical indicators.
    """
    def __init__(self, agent_id: str = "technical_agent", agent_type: AgentType = AgentType.TECHNICAL, message_broker: MessageBrokerInterface = None, broker: Optional[BrokerInterface] = None, persona: Dict[str, Any] = None, api_client: Any = None, config: Any = None, database: Any = None):
        super().__init__(agent_id=agent_id, agent_type=AgentType.TECHNICAL, message_broker=message_broker, broker=broker, persona=persona or {})
        self.message_broker = message_broker
        self.broker = broker
        self.api_client = api_client
        self.config = config
        self.database = database
        self.is_running = False
        self.technical_signals: Dict[str, Any] = {"RSI": "neutral", "MACD": "neutral", "last_scan": None}
        self.latest_market_data: Dict[str, Dict[str, Any]] = {}
        self.ohlcv_history: Dict[str, pd.DataFrame] = {}
        self.market_data_ingestor = MarketDataIngestor(self.broker)
        self.analytics_engine = AnalyticsEngine()
        
        # Initialize MATLAB integration
        self.matlab_engine = get_matlab_engine()
        if self.matlab_engine.is_available():
            logger.info(f"Priv Technical Agent '{self.agent_id}' initialized with MATLAB integration ✅")
        else:
            logger.info(f"Priv Technical Agent '{self.agent_id}' initialized (MATLAB not available)")
        
        logger.info(f"Priv Technical Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the technical agent."""
        if self.is_running:
            logger.warning(f"Technical Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to real-time market data
        await self.message_broker.subscribe_to_topic(
            "real_time_market_data", self._handle_real_time_market_data, f"{self.agent_id}-market-data-sub"
        )
        
        self.is_running = True
        # Start a periodic task to refresh historical data and generate proposals
        self._periodic_analysis_task = asyncio.create_task(self._periodic_technical_analysis())
        logger.info(f"Priv Technical Agent '{self.agent_id}' started and subscribed to 'real_time_market_data'.")

    async def stop(self):
        """Stops the technical agent."""
        if not self.is_running:
            logger.warning(f"Technical Agent '{self.agent_id}' is not running.")
            return
        
        self.is_running = False
        if self._periodic_analysis_task:
            self._periodic_analysis_task.cancel()
            try:
                await self._periodic_analysis_task
            except asyncio.CancelledError:
                logger.info(f"Priv Technical Agent '{self.agent_id}' periodic analysis task cancelled.")
        
        logger.info(f"Priv Technical Agent '{self.agent_id}' stopped.")

    async def _periodic_technical_analysis(self):
        """
        Periodically fetches historical data, performs technical analysis,
        and generates trade proposals for configured symbols.
        """
        while self.is_running:
            try:
                logger.info(f"Priv Technical Agent '{self.agent_id}': Initiating periodic technical analysis.")
                
                # Symbols to analyze (could be configurable in settings)
                symbols_to_analyze = settings.TECHNICAL_AGENT_SYMBOLS_TO_ANALYZE

                for symbol in symbols_to_analyze:
                    logger.info(f"Technical Agent: Fetching historical data for {symbol}...")
                    # Fetch daily data for a reasonable lookback period
                    historical_df = await get_market_data(
                        symbol=symbol, 
                        timeframe=settings.TECHNICAL_AGENT_TIMEFRAME, 
                        num_bars=settings.TECHNICAL_AGENT_LOOKBACK_BARS
                    )
                    
                    if historical_df is not None and not historical_df.empty:
                        self.ohlcv_history[symbol] = historical_df
                        logger.info(f"Technical Agent: Fetched {len(historical_df)} bars for {symbol}.")
                        
                        # Now generate a trade proposal based on this refreshed data
                        await self.generate_trade_proposal(symbol)
                    else:
                        logger.warning(f"Technical Agent: No historical data fetched for {symbol}. Skipping analysis.")
                    
                    await asyncio.sleep(settings.TECHNICAL_AGENT_SYMBOL_DELAY_SECONDS) # Small delay between symbols

            except Exception as e:
                logger.error(f"Priv Technical Agent '{self.agent_id}': Error during periodic technical analysis: {e}", exc_info=True)
            
            await asyncio.sleep(settings.TECHNICAL_AGENT_ANALYSIS_INTERVAL_SECONDS) # Main interval

    async def _handle_real_time_market_data(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming real-time market data messages.
        Updates the agent's internal state with the latest prices and triggers immediate analysis.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            market_data_item = agent_message.payload # Assuming payload is the market data dict

            symbol = market_data_item.get("symbol")
            if not symbol:
                logger.warning(f"Technical Agent: Received market data without a symbol: {market_data_item}")
                return

            # Store the latest market data for this symbol
            self.latest_market_data[symbol] = market_data_item
            logger.debug(f"Technical Agent '{self.agent_id}' updated live data for {symbol}: {market_data_item.get('last_trade_price', 'N/A')}")

            # Trigger immediate analysis if this is a critical symbol or if configured for high frequency
            if symbol in settings.TECHNICAL_AGENT_CRITICAL_SYMBOLS_FOR_REALTIME_ANALYSIS:
                # Append latest real-time data to historical data for up-to-date analysis
                current_price = market_data_item.get('last_trade_price')
                if current_price is not None and symbol in self.ohlcv_history:
                    # Create a dummy row for the latest data point
                    new_row_data = {
                        'open': market_data_item.get('open_price', current_price),
                        'high': market_data_item.get('high_price', current_price),
                        'low': market_data_item.get('low_price', current_price),
                        'close': current_price,
                        'volume': market_data_item.get('volume', 0),
                    }
                    # Ensure timestamp is a datetime object
                    timestamp_str = market_data_item.get('timestamp')
                    if timestamp_str:
                        try:
                            # Handle various ISO formats or numeric timestamps
                            if isinstance(timestamp_str, (int, float)):
                                new_timestamp = datetime.fromtimestamp(timestamp_str / 1000) # Assuming milliseconds
                            else:
                                new_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        except ValueError:
                            new_timestamp = datetime.now() # Fallback
                    else:
                        new_timestamp = datetime.now()

                    new_row_df = pd.DataFrame([new_row_data], index=[new_timestamp])
                    new_row_df.index.name = 'timestamp'
                    
                    # Append and keep only the latest N bars
                    combined_df = pd.concat([self.ohlcv_history[symbol], new_row_df]).drop_duplicates(keep='last')
                    self.ohlcv_history[symbol] = combined_df.tail(settings.TECHNICAL_AGENT_LOOKBACK_BARS)

                    logger.debug(f"Technical Agent: Appended real-time data for {symbol}. Triggering immediate proposal generation.")
                    await self.generate_trade_proposal(symbol)


        except Exception as e:
            logger.error(f"Technical Agent '{self.agent_id}': Error processing real-time market data message: {e}", exc_info=True)


    async def generate_trade_proposal(self, symbol: str) -> Optional[TradeProposal]:
        """
        Generates a trade proposal based on technical analysis signals from live and historical data.
        """
        logger.info(f"Technical Agent '{self.agent_id}' is performing technical analysis for {symbol}...")

        historical_df = self.ohlcv_history.get(symbol)
        live_data = self.latest_market_data.get(symbol)

        if historical_df is None or historical_df.empty:
            logger.warning(f"Technical Agent: No sufficient historical data for {symbol}. Cannot generate proposal.")
            return None
        
        if live_data is None:
            logger.warning(f"Technical Agent: No live market data available for {symbol}. Cannot generate proposal.")
            return None

        current_price = live_data.get("last_trade_price")
        if current_price is None:
            logger.warning(f"Technical Agent: Live data for {symbol} missing 'last_trade_price'. Cannot generate proposal.")
            return None
        
        # Ensure the historical_df is sorted by timestamp
        historical_df = historical_df.sort_index()

        # --- Perform Technical Analysis using AnalyticsEngine ---
        # Direct call to AnalyticsEngine as it's confirmed to be available and functional
        try:
            # AnalyticsEngine expects OHLCV with 'open', 'high', 'low', 'close', 'volume'
            analysis_results = self.analytics_engine.calculate_indicators(historical_df)
            logger.debug(f"Technical Agent: AnalyticsEngine calculated indicators for {symbol}.")
        except Exception as e:
            logger.error(f"Technical Agent: Critical error running AnalyticsEngine for {symbol}: {e}", exc_info=True)
            # If AnalyticsEngine fails, this is a critical issue for a live system.
            # You might want to publish a critical alert here.
            return None # Cannot proceed without technical analysis

        # Extract latest indicator values
        latest_indicators = analysis_results.get('standard_indicators', {})
        # For indicators returned as lists, take the last element
        latest_rsi = latest_indicators.get('rsi', [50.0])[-1] if isinstance(latest_indicators.get('rsi'), list) else 50.0
        latest_macd_hist = latest_indicators.get('macd_hist', [0.0])[-1] if isinstance(latest_indicators.get('macd_hist'), list) else 0.0
        latest_sma20 = latest_indicators.get('sma20', [current_price])[-1] if isinstance(latest_indicators.get('sma20'), list) else current_price

        # --- Generate Trade Signal based on Technical Indicators ---
        action = TradeAction.HOLD
        confidence = 0.5
        reasoning = f"Technical analysis for {symbol} indicates no clear signal or insufficient data for comprehensive analysis."

        # Example: RSI and MACD based strategy
        # Configurable thresholds from settings
        RSI_OVERBOUGHT = getattr(settings, 'TECHNICAL_RSI_OVERBOUGHT', 70)
        RSI_OVERSOLD = getattr(settings, 'TECHNICAL_RSI_OVERSOLD', 30)
        MACD_BULLISH_THRESHOLD = getattr(settings, 'TECHNICAL_MACD_BULLISH_THRESHOLD', 0.1)
        MACD_BEARISH_THRESHOLD = getattr(settings, 'TECHNICAL_MACD_BEARISH_THRESHOLD', -0.1)
        SMA_CROSSOVER_THRESHOLD = getattr(settings, 'TECHNICAL_SMA_CROSSOVER_THRESHOLD_PCT', 0.005) # 0.5% difference

        bullish_signals = 0
        bearish_signals = 0
        
        # RSI Signal
        if latest_rsi < RSI_OVERSOLD:
            bullish_signals += 1
            reasoning = "RSI oversold, suggesting potential rebound."
        elif latest_rsi > RSI_OVERBOUGHT:
            bearish_signals += 1
            reasoning = "RSI overbought, suggesting potential pullback."

        # MACD Signal (using histogram for momentum)
        if latest_macd_hist > MACD_BULLISH_THRESHOLD:
            bullish_signals += 1
            reasoning += " MACD histogram turning positive, indicating bullish momentum."
        elif latest_macd_hist < MACD_BEARISH_THRESHOLD:
            bearish_signals += 1
            reasoning += " MACD histogram turning negative, indicating bearish momentum."

        # Simple Moving Average Crossover (e.g., price vs SMA20)
        if current_price > latest_sma20 * (1 + SMA_CROSSOVER_THRESHOLD):
            bullish_signals += 1
            reasoning += " Price significantly above SMA20, confirming bullish trend."
        elif current_price < latest_sma20 * (1 - SMA_CROSSOVER_THRESHOLD):
            bearish_signals += 1
            reasoning += " Price significantly below SMA20, confirming bearish trend."

        # Determine action and confidence based on signal count
        if bullish_signals > bearish_signals and bullish_signals >= settings.TECHNICAL_MIN_CONFIRMATIONS:
            action = TradeAction.BUY
            confidence = min(1.0, 0.5 + (bullish_signals * settings.TECHNICAL_CONFIDENCE_PER_SIGNAL))
        elif bearish_signals > bullish_signals and bearish_signals >= settings.TECHNICAL_MIN_CONFIRMATIONS:
            action = TradeAction.SELL
            confidence = min(1.0, 0.5 + (bearish_signals * settings.TECHNICAL_CONFIDENCE_PER_SIGNAL))
        else:
            action = TradeAction.HOLD
            confidence = 0.5 # Default confidence for HOLD

        self.technical_signals[symbol] = {
            "current_price": current_price,
            "signal_generated_at": datetime.now().isoformat(),
            "action": action.value,
            "rsi": latest_rsi,
            "macd_hist": latest_macd_hist,
            "sma20": latest_sma20,
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals
        }

        prop = TradeProposal(
            agent_id=self.agent_id,
            symbol=symbol,
            action=action,
            volume=settings.TECHNICAL_TRADE_PROPOSAL_VOLUME, # Configurable volume
            entry_price=current_price,
            reasoning=reasoning,
            confidence=confidence,
            risk_assessment={"technical_risk": "moderate", "volatility": "average", "signals_count": max(bullish_signals, bearish_signals)}
        )
        logger.info(f"Technical Agent '{self.agent_id}' generated proposal: {prop.action} {prop.symbol} with confidence {prop.confidence:.2f}.")
        
        # Publish the proposal to the trade_proposals topic
        await self.broker.publish_message("trade_proposals", prop.model_dump())
        return prop


# Example Usage (for testing PrivTechnicalAgent in isolation)
async def main_technical_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings
    from unittest.mock import patch, MagicMock # Needed for test patching
    import numpy as np # For mock data

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    # Set dummy values for settings if not already present for local testing
    if not hasattr(settings, 'TECHNICAL_AGENT_SYMBOLS_TO_ANALYZE'):
        settings.TECHNICAL_AGENT_SYMBOLS_TO_ANALYZE = ["EURUSD", "GBPUSD"]
    if not hasattr(settings, 'TECHNICAL_AGENT_TIMEFRAME'):
        settings.TECHNICAL_AGENT_TIMEFRAME = "daily"
    if not hasattr(settings, 'TECHNICAL_AGENT_LOOKBACK_BARS'):
        settings.TECHNICAL_AGENT_LOOKBACK_BARS = 250
    if not hasattr(settings, 'TECHNICAL_AGENT_SYMBOL_DELAY_SECONDS'):
        settings.TECHNICAL_AGENT_SYMBOL_DELAY_SECONDS = 0.5
    if not hasattr(settings, 'TECHNICAL_AGENT_ANALYSIS_INTERVAL_SECONDS'):
        settings.TECHNICAL_AGENT_ANALYSIS_INTERVAL_SECONDS = 10 # Frequent for test
    if not hasattr(settings, 'TECHNICAL_AGENT_CRITICAL_SYMBOLS_FOR_REALTIME_ANALYSIS'):
        settings.TECHNICAL_AGENT_CRITICAL_SYMBOLS_FOR_REALTIME_ANALYSIS = ["EURUSD"]
    if not hasattr(settings, 'TECHNICAL_RSI_OVERBOUGHT'):
        settings.TECHNICAL_RSI_OVERBOUGHT = 70
    if not hasattr(settings, 'TECHNICAL_RSI_OVERSOLD'):
        settings.TECHNICAL_RSI_OVERSOLD = 30
    if not hasattr(settings, 'TECHNICAL_MACD_BULLISH_THRESHOLD'):
        settings.TECHNICAL_MACD_BULLISH_THRESHOLD = 0.1
    if not hasattr(settings, 'TECHNICAL_MACD_BEARISH_THRESHOLD'):
        settings.TECHNICAL_MACD_BEARISH_THRESHOLD = -0.1
    if not hasattr(settings, 'TECHNICAL_SMA_CROSSOVER_THRESHOLD_PCT'):
        settings.TECHNICAL_SMA_CROSSOVER_THRESHOLD_PCT = 0.005
    if not hasattr(settings, 'TECHNICAL_MIN_CONFIRMATIONS'):
        settings.TECHNICAL_MIN_CONFIRMATIONS = 2
    if not hasattr(settings, 'TECHNICAL_CONFIDENCE_PER_SIGNAL'):
        settings.TECHNICAL_CONFIDENCE_PER_SIGNAL = 0.15
    if not hasattr(settings, 'TECHNICAL_TRADE_PROPOSAL_VOLUME'):
        settings.TECHNICAL_TRADE_PROPOSAL_VOLUME = 0.05


    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    technical_agent = PrivTechnicalAgent(
        agent_id="Priv-Technical",
        broker=broker,
        persona={"name": "Technical Analyst", "focus": "Chart Patterns"}
    )

    await broker.connect()
    await technical_agent.start()

    # Mock get_market_data to return a dummy DataFrame
    mock_df_length = 260 # Enough for 250 bars + some for indicators
    mock_dates = pd.date_range(start='2023-01-01', periods=mock_df_length, freq='D')
    mock_closes_eurusd = 1.08 + np.cumsum(np.random.normal(0, 0.001, mock_df_length))
    mock_opens_eurusd = mock_closes_eurusd - np.random.uniform(-0.0005, 0.0005, mock_df_length)
    mock_highs_eurusd = np.maximum(mock_opens_eurusd, mock_closes_eurusd) + np.random.uniform(0, 0.0008, mock_df_length)
    mock_lows_eurusd = np.minimum(mock_opens_eurusd, mock_closes_eurusd) - np.random.uniform(0, 0.0008, mock_df_length)
    mock_volumes = np.random.randint(1000, 5000, mock_df_length)

    mock_historical_eurusd_df = pd.DataFrame({
        'open': mock_opens_eurusd, 'high': mock_highs_eurusd, 'low': mock_lows_eurusd, 
        'close': mock_closes_eurusd, 'volume': mock_volumes
    }, index=mock_dates)
    mock_historical_eurusd_df.index.name = 'timestamp'


    mock_closes_gbpusd = 1.25 + np.cumsum(np.random.normal(0, 0.0008, mock_df_length))
    mock_opens_gbpusd = mock_closes_gbpusd - np.random.uniform(-0.0004, 0.0004, mock_df_length)
    mock_highs_gbpusd = np.maximum(mock_opens_gbpusd, mock_closes_gbpusd) + np.random.uniform(0, 0.0007, mock_df_length)
    mock_lows_gbpusd = np.minimum(mock_opens_gbpusd, mock_closes_gbpusd) - np.random.uniform(0, 0.0007, mock_df_length)
    mock_historical_gbpusd_df = pd.DataFrame({
        'open': mock_opens_gbpusd, 'high': mock_highs_gbpusd, 'low': mock_lows_gbpusd, 
        'close': mock_closes_gbpusd, 'volume': mock_volumes
    }, index=mock_dates)
    mock_historical_gbpusd_df.index.name = 'timestamp'


    with patch('backend.data_sourcing.data_loader.get_market_data') as mock_get_market_data:
        mock_get_market_data.side_effect = lambda symbol, **kwargs: {
            "EURUSD": mock_historical_eurusd_df,
            "GBPUSD": mock_historical_gbpusd_df,
            "AUDCAD": pd.DataFrame() # No data for this one
        }.get(symbol)

        # Mock AnalyticsEngine.calculate_indicators to return a predictable output for testing
        # This is crucial for isolated testing of the agent's logic, without running full TA-Lib
        with patch('backend.support_ai.analytics_engine.AnalyticsEngine.calculate_indicators') as mock_calculate_indicators:
            mock_calculate_indicators.return_value = {
                "standard_indicators": {
                    "rsi": [60.0] * mock_df_length,  # Example: RSI not oversold/overbought
                    "macd_hist": [0.05] * mock_df_length, # Example: slightly bullish MACD
                    "sma20": (mock_closes_eurusd * 0.99).tolist() # Example: price slightly above SMA
                }
                # Other analytics results can be mocked here if needed by the agent's logic
            }

            logger.info("\n--- Simulating real-time market data arrival for Technical Agent ---")
            # This is what _handle_real_time_market_data would receive
            mock_live_data_eurusd = AgentMessage(
                sender_id="MarketDataIngestor",
                message_type=MessageType.STATUS_UPDATE,
                payload={
                    "symbol": "EURUSD",
                    "bid_price": mock_closes_eurusd[-1] - 0.0002,
                    "ask_price": mock_closes_eurusd[-1] + 0.0002,
                    "last_trade_price": mock_closes_eurusd[-1] + 0.0001, # Slightly higher to trigger buy
                    "timestamp": datetime.now().timestamp() * 1e9, # Nanoseconds
                    "source": "Polygon.io",
                    "type": "market_data_quote",
                    "open_price": mock_opens_eurusd[-1],
                    "high_price": mock_highs_eurusd[-1],
                    "low_price": mock_lows_eurusd[-1],
                    "volume": mock_volumes[-1]
                }
            )
            await broker.publish_message("real_time_market_data", mock_live_data_eurusd.model_dump())
            await asyncio.sleep(1) # Give agent time to process the incoming data and run immediate analysis

            logger.info("\n--- Technical Agent generating proposals using internal live data (from periodic scan) ---")
            # The periodic scan task will now trigger analysis for configured symbols
            await asyncio.sleep(settings.TECHNICAL_AGENT_ANALYSIS_INTERVAL_SECONDS + 2) # Wait for first periodic run

            # Example of a symbol for which no data has arrived yet (or was mocked as empty)
            prop3 = await technical_agent.generate_trade_proposal("AUDCAD")
            if prop3:
                logger.info(f"Technical Agent Proposal 3 (AUDCAD): {prop3.action} {prop3.symbol} (Conf: {prop3.confidence:.2f})")
            else:
                logger.info("Technical Agent Proposal 3 (AUDCAD): No data available to generate proposal.")

    await asyncio.sleep(5) # Give time for remaining tasks
    await technical_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivTechnicalAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_technical_agent_test())
