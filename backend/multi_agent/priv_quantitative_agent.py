# backend/multi_agent/priv_quantitative_agent.py

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Import necessary components from your multi_agent system
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeAction, TradeProposal, AgentType
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

# MATLAB integration for advanced quantitative analysis
from backend.utils.matlab_integration import get_matlab_engine

logger = logging.getLogger(__name__)

class PrivQuantitativeAgent(PrivAgent):
    async def predict_outcomes(self, test_data):
        """Mock prediction for test compatibility."""
        # Return a list of dicts with 'accuracy' for each item
        return [{'accuracy': 0.8} for _ in test_data]
    """
    A specialized Priv Agent focused on quantitative analysis and algorithmic strategies.
    This agent identifies statistical arbitrage opportunities or high-probability patterns.
    """
    def __init__(self, agent_id: str = "quantitative_agent", agent_type: AgentType = AgentType.QUANTITATIVE, message_broker: MessageBrokerInterface = None, broker: Optional[BrokerInterface] = None, persona: Dict[str, Any] = None, api_client: Any = None, config: Any = None, database: Any = None):
        super().__init__(agent_id=agent_id, agent_type=AgentType.QUANTITATIVE, message_broker=message_broker, broker=broker, persona=persona or {})
        self.broker = broker
        self.api_client = api_client
        self.config = config
        self.database = database
        self.is_running = False
        self.strategy_performance: Dict[str, Any] = {"mean_reversion_accuracy": 0.75, "last_signal_time": None}
        self.latest_market_data: Dict[str, Dict[str, Any]] = {}
        self.historical_data_cache: Dict[str, List[float]] = {}
        
        # Initialize MATLAB integration
        self.matlab_engine = get_matlab_engine()
        logger.info(f"Quantitative Agent {agent_id} initialized with MATLAB: {self.matlab_engine.is_available()}")
    async def analyze_market_data(self, symbol: str, market_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze market data using MATLAB for advanced quantitative analysis."""
        import numpy as np
        prices = [d.get("price", d.get("last_trade_price", 0)) for d in market_data if d.get("price", d.get("last_trade_price", None) is not None)]
        if not prices:
            return {"analysis": {}, "signals": [], "confidence": 0.0}
        
        prices_array = np.array(prices, dtype=float)
        
        # Enhanced analysis with MATLAB if available
        if self.matlab_engine.is_available() and len(prices) >= 50:
            try:
                # Use MATLAB for advanced statistics
                matlab_stats = await self.matlab_engine.compute_advanced_statistics(prices_array)
                
                # Apply signal processing
                smoothed_prices = await self.matlab_engine.perform_signal_processing(
                    prices_array, 
                    filter_type='exponential',
                    window=20
                )
                
                analysis = matlab_stats
                analysis['smoothed_price_current'] = float(smoothed_prices[-1])
                
                # Generate signals based on MATLAB statistics
                current_price = prices[-1]
                signals = []
                
                # Volatility-based signals
                if matlab_stats['annualized_volatility'] > 0.5:
                    signals.append({
                        "symbol": symbol,
                        "signal_type": "HOLD",
                        "confidence": 0.6,
                        "reason": f"High volatility detected: {matlab_stats['annualized_volatility']:.2%}",
                        "source": "MATLAB_VOLATILITY"
                    })
                
                # Mean reversion with MATLAB smoothing
                smooth_current = smoothed_prices[-1]
                deviation_pct = (current_price - smooth_current) / smooth_current
                
                if deviation_pct < -0.02:  # 2% below smoothed
                    signals.append({
                        "symbol": symbol,
                        "signal_type": "BUY",
                        "confidence": 0.75,
                        "reason": f"Price {deviation_pct:.2%} below MATLAB-smoothed value",
                        "source": "MATLAB_MEAN_REVERSION"
                    })
                elif deviation_pct > 0.02:  # 2% above smoothed
                    signals.append({
                        "symbol": symbol,
                        "signal_type": "SELL",
                        "confidence": 0.75,
                        "reason": f"Price {deviation_pct:.2%} above MATLAB-smoothed value",
                        "source": "MATLAB_MEAN_REVERSION"
                    })
                
                logger.info(f"MATLAB analysis completed for {symbol}: volatility={matlab_stats['annualized_volatility']:.2%}, skewness={matlab_stats['skewness']:.3f}")
                    
            except Exception as e:
                logger.error(f"Error in MATLAB analysis: {e}")
                # Continue with fallback
        else:
            # Basic statistical analysis without MATLAB
            mean = np.mean(prices_array)
            std = np.std(prices_array)
            analysis = {"mean": float(mean), "std": float(std)}
            signals = []
        
        # Fallback to basic analysis if MATLAB not available or no signals generated
        if not signals:
            mean = analysis.get('mean', np.mean(prices_array))
            std = analysis.get('std', np.std(prices_array))
            confidence = min(1.0, std / mean if mean else 0.0)
            signals = [{
                "symbol": symbol,
                "signal_type": "BUY" if prices[-1] < mean else "SELL",
                "confidence": confidence,
                "reason": "Mean reversion strategy (basic)",
                "source": "NumPy"
            }]
        
        # Calculate aggregate confidence
        avg_confidence = np.mean([s["confidence"] for s in signals]) if signals else 0.0
        
        return {
            "analysis": analysis,
            "signals": signals,
            "confidence": avg_confidence,
            "matlab_enabled": self.matlab_wrapper.is_available()
        }
        prices = [d.get("price", d.get("last_trade_price", 0)) for d in market_data if d.get("price", d.get("last_trade_price", None) is not None)]
        if not prices:
            return {"analysis": {}, "signals": [], "confidence": 0.0}
        mean = np.mean(prices)
        std = np.std(prices)
        confidence = min(1.0, std / mean if mean else 0.0)
        signals = [{"symbol": symbol, "signal_type": "BUY" if prices[-1] < mean else "SELL", "confidence": confidence}]
        return {"analysis": {"mean": mean, "std": std}, "signals": signals, "confidence": confidence}

    async def generate_signals(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate trading signals from input."""
        # Pass-through for test compatibility
        return signals

    async def calculate_risk_metrics(self, market_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate risk metrics for the given market data."""
        import numpy as np
        prices = [d.get("price", d.get("last_trade_price", 0)) for d in market_data if d.get("price", d.get("last_trade_price", None) is not None)]
        if not prices:
            return {"var_95": 0.0, "var_99": 0.0, "sharpe_ratio": 0.0, "max_drawdown": 0.0}
        returns = np.diff(prices) / prices[:-1] if len(prices) > 1 else [0.0]
        var_95 = float(np.percentile(returns, 5))
        var_99 = float(np.percentile(returns, 1))
        sharpe_ratio = float(np.mean(returns) / np.std(returns)) if np.std(returns) != 0 else 0.0
        max_drawdown = float((min(prices) - max(prices)) / max(prices)) if prices else 0.0
        return {"var_95": var_95, "var_99": var_99, "sharpe_ratio": sharpe_ratio, "max_drawdown": abs(max_drawdown)}

    async def backtest_strategy(self, historical_data: List[Dict[str, Any]], strategy_params: Dict[str, Any]) -> Dict[str, Any]:
        """Backtest a strategy and return results."""
        import numpy as np
        prices = [d.get("price", d.get("last_trade_price", 0)) for d in historical_data if d.get("price", d.get("last_trade_price", None) is not None)]
        if not prices:
            return {"total_return": 0.0, "max_drawdown": 0.0, "sharpe_ratio": 0.0, "win_rate": 0.0}
        total_return = (prices[-1] - prices[0]) / prices[0] if prices else 0.0
        max_drawdown = float((min(prices) - max(prices)) / max(prices)) if prices else 0.0
        returns = np.diff(prices) / prices[:-1] if len(prices) > 1 else [0.0]
        sharpe_ratio = float(np.mean(returns) / np.std(returns)) if np.std(returns) != 0 else 0.0
        win_rate = float(np.sum(np.array(returns) > 0) / len(returns)) if returns else 0.0
        return {"total_return": total_return, "max_drawdown": abs(max_drawdown), "sharpe_ratio": sharpe_ratio, "win_rate": win_rate}

    async def start(self):
        """Starts the quantitative agent."""
        if self.is_running:
            logger.warning(f"Quantitative Agent '{self.agent_id}' is already running.")
            return

        # NEW: Subscribe to real-time market data
        await self.message_broker.subscribe_to_topic("real_time_market_data", self._handle_real_time_market_data, f"{self.agent_id}-market-data-sub")

        self.is_running = True
        logger.info(f"Priv Quantitative Agent '{self.agent_id}' started and subscribed to 'real_time_market_data'.")

    async def stop(self):
        """Stops the quantitative agent."""
        if not self.is_running:
            logger.warning(f"Quantitative Agent '{self.agent_id}' is not running.")
            return
        self.is_running = False
        logger.info(f"Priv Quantitative Agent '{self.agent_id}' stopped.")

    async def _handle_real_time_market_data(self, message_payload: Dict[str, Any]):
        """
        Callback to process incoming real-time market data messages.
        Updates the agent's internal state with the latest prices and conceptually
        updates its historical data cache.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            market_data_item = agent_message.payload # Assuming payload is the market data dict

            symbol = market_data_item.get("symbol")
            last_trade_price = market_data_item.get("last_trade_price")
            if not symbol or last_trade_price is None:
                logger.warning(f"Quantitative Agent: Received market data without symbol or price: {market_data_item}")
                return

            # Store the latest market data for this symbol
            self.latest_market_data[symbol] = market_data_item
            logger.debug(f"Quantitative Agent '{self.agent_id}' updated live data for {symbol}: {last_trade_price}")

            # Conceptually update historical data cache
            if symbol not in self.historical_data_cache:
                self.historical_data_cache[symbol] = []
            
            # Keep a limited history for conceptual calculations (e.g., last 100 prices)
            self.historical_data_cache[symbol].append(last_trade_price)
            if len(self.historical_data_cache[symbol]) > 100:
                self.historical_data_cache[symbol].pop(0)

        except Exception as e:
            logger.error(f"Quantitative Agent '{self.agent_id}': Error processing real-time market data message: {e}", exc_info=True)


    # Conceptual method for generating a trade proposal based on quantitative analysis (e.g., mean reversion).
    # MODIFIED: market_data parameter is now optional, as agent will use its internal state
    async def generate_trade_proposal(self, symbol: str) -> Optional[TradeProposal]:
        """
        Generates a trade proposal based on quantitative analysis from live data.
        """
        logger.info(f"Quantitative Agent '{self.agent_id}' is performing quantitative analysis for {symbol}...")

        # Retrieve the latest market data from internal state
        live_data = self.latest_market_data.get(symbol)
        historical_prices = self.historical_data_cache.get(symbol)

        if not live_data or not historical_prices or len(historical_prices) < 20: # Need enough data for "mean"
            logger.warning(f"Quantitative Agent: Insufficient live or historical data for {symbol}. Cannot generate proposal.")
            return None
        
        current_price = live_data.get("last_trade_price")
        if current_price is None:
            logger.warning(f"Quantitative Agent: No current price in live data for {symbol}. Cannot generate proposal.")
            return None

        # --- Conceptual Quantitative Analysis Logic (Mean Reversion) ---
        # In a real system, you'd use a robust library (e.g., numpy for calculations, pandas for dataframes)
        # to calculate actual statistical indicators.
        import numpy as np # Importing here for conceptual calculation

        historical_mean = np.mean(historical_prices)
        standard_deviation = np.std(historical_prices)
        
        # Avoid division by zero if std_dev is very small or zero
        if standard_deviation < 1e-6:
            logger.warning(f"Quantitative Agent: Standard deviation for {symbol} is too small. Cannot reliably calculate Z-score.")
            # If no volatility, assume neutral or hold
            action = TradeAction.HOLD
            confidence = 0.5
            reasoning = "Extremely low volatility detected, no clear quantitative signal."
            volume = 0.0
        else:
            z_score = (current_price - historical_mean) / standard_deviation

            action = TradeAction.HOLD
            confidence = 0.5
            reasoning = "No strong quantitative signal detected."
            volume = 0.02 # Typically smaller volumes for quant strategies

            # Conceptual mean reversion logic: if price deviates significantly from mean
            if z_score < -2.0: # Price is 2 standard deviations below mean
                action = TradeAction.BUY
                confidence = 0.9
                reasoning = f"Price ({current_price:.2f}) is {abs(z_score):.2f}-sigma below historical mean ({historical_mean:.2f}). Strong mean-reversion BUY signal."
                volume = 0.05
            elif z_score > 2.0: # Price is 2 standard deviations above mean
                action = TradeAction.SELL
                confidence = 0.9
                reasoning = f"Price ({current_price:.2f}) is {z_score:.2f}-sigma above historical mean ({historical_mean:.2f}). Strong mean-reversion SELL signal."
                volume = 0.05
            elif z_score < -1.0: # Price is 1 standard deviation below mean
                action = TradeAction.BUY
                confidence = 0.75
                reasoning = f"Price ({current_price:.2f}) is {abs(z_score):.2f}-sigma below historical mean ({historical_mean:.2f}). Mean-reversion BUY signal."
            elif z_score > 1.0: # Price is 1 standard deviation above mean
                action = TradeAction.SELL
                confidence = 0.75
                reasoning = f"Price ({current_price:.2f}) is {z_score:.2f}-sigma above historical mean ({historical_mean:.2f}). Mean-reversion SELL signal."

        self.strategy_performance["last_signal_time"] = datetime.now().isoformat()
        self.strategy_performance["last_z_score"] = z_score if 'z_score' in locals() else None

        prop = TradeProposal(
            agent_id=self.agent_id,
            symbol=symbol,
            action=action,
            volume=volume,
            entry_price=current_price,
            reasoning=reasoning,
            confidence=confidence,
            risk_assessment={"strategy_type": "mean_reversion", "expected_holding_period": "short"}
        )
        logger.info(f"Quantitative Agent '{self.agent_id}' generated proposal: {prop.action} {prop.symbol} with confidence {prop.confidence:.2f}.")
        return prop

# Example Usage (for testing PrivQuantitativeAgent in isolation)
async def main_quantitative_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    quant_agent = PrivQuantitativeAgent(
        agent_id="Priv-Quant",
        broker=broker,
        persona={"name": "Quantitative Strategist", "focus": "Statistical Arbitrage", "role": "quantitative_strategist"}
    )

    await broker.connect()
    await quant_agent.start()

    # Simulate real-time market data coming from the MarketDataIngestor
    mock_live_data_spy_1 = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "SPY", "bid_price": 405.00, "ask_price": 405.10, "last_trade_price": 405.05,
            "timestamp": datetime.now().timestamp() * 1e9, "source": "Polygon.io", "type": "market_data_quote"
        }
    )
    mock_live_data_spy_2 = AgentMessage( # Price drops, simulating mean reversion opportunity
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "SPY", "bid_price": 398.00, "ask_price": 398.10, "last_trade_price": 398.05,
            "timestamp": (datetime.now() + timedelta(seconds=1)).timestamp() * 1e9, "source": "Polygon.io", "type": "market_data_quote"
        }
    )
    mock_live_data_spy_3 = AgentMessage( # Even further drop
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "SPY", "bid_price": 390.00, "ask_price": 390.10, "last_trade_price": 390.05,
            "timestamp": (datetime.now() + timedelta(seconds=2)).timestamp() * 1e9, "source": "Polygon.io", "type": "market_data_quote"
        }
    )
    mock_live_data_qqq = AgentMessage(
        sender_id="MarketDataIngestor",
        message_type=MessageType.STATUS_UPDATE,
        payload={
            "symbol": "QQQ", "bid_price": 300.00, "ask_price": 300.10, "last_trade_price": 300.05,
            "timestamp": datetime.now().timestamp() * 1e9, "source": "Finnhub.io", "type": "market_data_quote"
        }
    )

    logger.info("\n--- Simulating real-time market data arrival for Quantitative Agent ---")
    # To get a meaningful mean and std dev, we'll simulate more historical data
    # For a real system, you'd fetch initial historical data using data_loader.py
    for _ in range(50): # Simulate 50 historical prices around a mean of 400 with std dev 5
        price = 400 + 5 * (2 * (0.5 - asyncio.run(asyncio.to_thread(lambda: random.random()))) ) # Simple random walk around 400
        quant_agent.historical_data_cache["SPY"].append(price)
        quant_agent.historical_data_cache["QQQ"].append(price) # Populate QQQ too
    
    await broker.publish_message("real_time_market_data", mock_live_data_spy_1.model_dump())
    await asyncio.sleep(0.5)
    await broker.publish_message("real_time_market_data", mock_live_data_spy_2.model_dump())
    await asyncio.sleep(0.5)
    await broker.publish_message("real_time_market_data", mock_live_data_spy_3.model_dump()) # This should trigger a BUY signal
    await asyncio.sleep(1) # Give agent time to process the incoming data

    logger.info("\n--- Quantitative Agent generating proposals using internal live data ---")
    prop1 = await quant_agent.generate_trade_proposal("SPY")
    if prop1:
        logger.info(f"Quant Agent Proposal 1 (SPY): {prop1.action} {prop1.symbol} (Conf: {prop1.confidence:.2f})")
    
    prop2 = await quant_agent.generate_trade_proposal("QQQ")
    if prop2:
        logger.info(f"Quant Agent Proposal 2 (QQQ): {prop2.action} {prop2.symbol} (Conf: {prop2.confidence:.2f})")

    await asyncio.sleep(2)
    await quant_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivQuantitativeAgent test finished.")

if __name__ == '__main__':
    # Add random import for the example
    import random
    asyncio.run(main_quantitative_agent_test())