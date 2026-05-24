import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class MarketSimulator:
    """
    Simulates market environments for Priv's decision rehearsals and stress testing.
    It can replay historical data and inject various market "shocks" or mutations.
    This is Priv's Market Replay & Mutation Engine.
    """
    def __init__(self, historical_data: pd.DataFrame):
        """
        Initializes the MarketSimulator with historical OHLCV data.

        Args:
            historical_data (pd.DataFrame): A DataFrame of OHLCV data with a DatetimeIndex.
                                            Expected columns: 'open', 'high', 'low', 'close', 'volume'.
        """
        if historical_data.empty or not all(col in historical_data.columns for col in ['open', 'high', 'low', 'close', 'volume']):
            logger.error("Priv: MarketSimulator initialized with empty or incomplete historical data. Simulation will be limited.")
            self.historical_data = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'], index=pd.to_datetime([]))
        else:
            self.historical_data = historical_data.sort_index() # Ensure data is sorted by time
        
        self.current_bar_index = -1 # Index of the current bar being "replayed"
        self.max_bars = len(self.historical_data)
        self.is_simulation_active = False
        self.shock_injections_scheduled: List[Dict[str, Any]] = [] # List of {"type": "flash_crash", "at_index": X, "magnitude": Y}
        logger.info(f"Priv's MarketSimulator initialized with {self.max_bars} historical bars.")

    def start_simulation(self) -> bool:
        """Starts the market simulation from the beginning of the historical data."""
        if self.max_bars == 0:
            logger.warning("Priv: Cannot start simulation: No historical data loaded.")
            return False
        self.current_bar_index = 0
        self.is_simulation_active = True
        self.shock_injections_scheduled = [] # Clear any previous shocks
        logger.info("Priv: Market simulation started.")
        return True

    def get_current_bar(self) -> Optional[pd.Series]:
        """Returns the current market bar in the simulation."""
        if not self.is_simulation_active or self.current_bar_index >= self.max_bars:
            return None
        return self.historical_data.iloc[self.current_bar_index]

    def advance_bar(self) -> Optional[pd.Series]:
        """Advances the simulation by one bar (tick/period)."""
        if not self.is_simulation_active or self.current_bar_index >= self.max_bars - 1:
            self.is_simulation_active = False
            logger.info("Priv: Market simulation finished (all bars replayed).")
            return None
        
        self.current_bar_index += 1
        current_bar = self.historical_data.iloc[self.current_bar_index].copy() # Get a copy to potentially modify

        # Apply any scheduled shock injections to the current bar
        for shock in self.shock_injections_scheduled:
            if shock["at_index"] == self.current_bar_index:
                self._apply_shock_to_bar(current_bar, shock)
                logger.info(f"Priv: Shock injected at bar {self.current_bar_index}: {shock['type']}")
        
        return current_bar

    def inject_shock(self, shock_type: str, bar_index: int, parameters: Dict[str, Any]):
        """
        Schedules a market "shock" to be injected at a specific bar index.
        This enables adversarial mutations and stress tests.

        Args:
            shock_type (str): Type of shock (e.g., "flash_crash", "volatility_spike", "liquidity_drain").
            bar_index (int): The index of the bar at which to inject the shock.
            parameters (Dict[str, Any]): Parameters for the shock (e.g., {"magnitude": 0.05} for flash_crash).
        """
        if bar_index < self.current_bar_index:
            logger.warning(f"Priv: Cannot inject shock at past index {bar_index}. Current bar is {self.current_bar_index}.")
            return
        if bar_index >= self.max_bars:
            logger.warning(f"Priv: Cannot inject shock at future index {bar_index}. Max bars: {self.max_bars}.")
            return

        shock_details = {"type": shock_type, "at_index": bar_index, "params": parameters}
        self.shock_injections_scheduled.append(shock_details)
        logger.info(f"Priv: Scheduled {shock_type} shock at index {bar_index}.")

    def _apply_shock_to_bar(self, bar: pd.Series, shock: Dict[str, Any]):
        """Applies the specified shock mutation to a given bar."""
        shock_type = shock["type"]
        params = shock["params"]

        if shock_type == "flash_crash":
            magnitude = params.get("magnitude", 0.05) # e.g., 0.05 for 5% drop
            logger.info(f"Priv: Applying flash crash of {magnitude:.2%} to bar {bar.name}.")
            # Simulate a sharp drop and then partial recovery within the bar
            original_close = bar['close']
            bar['low'] = bar['low'] * (1 - magnitude)
            bar['close'] = bar['close'] * (1 - magnitude * random.uniform(0.5, 0.9)) # Recover partially
            bar['open'] = bar['open'] * (1 - magnitude * random.uniform(0.1, 0.3)) # Open slightly lower
            bar['high'] = max(bar['high'], original_close) # Ensure high is not below original close if it was the high
            
        elif shock_type == "volatility_spike":
            multiplier = params.get("multiplier", 2.0) # Double the range
            logger.info(f"Priv: Applying volatility spike (range x{multiplier}) to bar {bar.name}.")
            mid_price = (bar['high'] + bar['low']) / 2
            current_range = bar['high'] - bar['low']
            new_range = current_range * multiplier
            bar['high'] = mid_price + new_range / 2
            bar['low'] = mid_price - new_range / 2
            
        elif shock_type == "compliance_violation_flag":
            # This type of shock doesn't alter price data but flags the context
            # In a full simulation, this would flag the 'current_context' passed to Priv's decision
            # For now, just log the event.
            logger.info(f"Priv: Simulated compliance violation event flagged at bar {bar.name}.")

        # Ensure OHLC integrity after shock
        bar['high'] = max(bar['high'], bar['open'], bar['close'], bar['low'])
        bar['low'] = min(bar['low'], bar['open'], bar['close'], bar['high'])


# Example Usage (for testing MarketSimulator in isolation)
async def main_market_simulator_test():
    logging.basicConfig(level=logging.INFO)

    # 1. Create Mock Historical Data
    data_length = 200
    dates = pd.date_range(start='2023-01-01', periods=data_length, freq='D')
    mock_closes = 100 + np.cumsum(np.random.normal(0, 0.5, data_length)) # Basic random walk
    mock_opens = mock_closes - np.random.uniform(-0.1, 0.1, data_length)
    mock_highs = np.maximum(mock_opens, mock_closes) + np.random.uniform(0, 0.2, data_length)
    mock_lows = np.minimum(mock_opens, mock_closes) - np.random.uniform(0, 0.2, data_length)
    mock_volumes = np.random.randint(1000, 5000, data_length)

    mock_df = pd.DataFrame({
        'open': mock_opens,
        'high': mock_highs,
        'low': mock_lows,
        'close': mock_closes,
        'volume': mock_volumes
    }, index=dates)
    mock_df.index.name = 'timestamp'
    logger.info(f"Mock historical data created with {len(mock_df)} bars.")

    # 2. Initialize MarketSimulator
    simulator = MarketSimulator(historical_data=mock_df)

    # 3. Schedule some shocks
    simulator.inject_shock("flash_crash", bar_index=50, parameters={"magnitude": 0.03}) # 3% crash
    simulator.inject_shock("volatility_spike", bar_index=100, parameters={"multiplier": 3.0}) # Triple volatility
    simulator.inject_shock("flash_crash", bar_index=150, parameters={"magnitude": 0.05}) # Another crash

    # 4. Start and run simulation
    if simulator.start_simulation():
        simulated_bars = []
        while simulator.is_simulation_active:
            current_bar = simulator.advance_bar()
            if current_bar is None:
                break
            simulated_bars.append(current_bar)
            
            if simulator.current_bar_index % 25 == 0:
                print(f"Simulating bar {simulator.current_bar_index}/{simulator.max_bars} - Close: {current_bar['close']:.2f}")

        simulated_df = pd.DataFrame(simulated_bars)
        print(f"\nSimulation finished. Total bars processed: {len(simulated_df)}")
        print("First 5 bars after simulation start:")
        print(simulated_df.head())
        print("\nLast 5 bars after simulation:")
        print(simulated_df.tail())

        # Check a shocked bar (e.g., bar 50, now at index 49 in simulated_df)
        if 49 < len(simulated_df):
            print(f"\nShocked bar (index 49): Original Close={mock_df.iloc[49]['close']:.2f}, Simulated Close={simulated_df.iloc[49]['close']:.2f}")

    else:
        print("Simulation could not be started.")

if __name__ == '__main__':
    # Use asyncio to run the async main_market_simulator_test function
    import asyncio
    asyncio.run(main_market_simulator_test())