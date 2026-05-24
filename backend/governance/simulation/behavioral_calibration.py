import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
import os
import json
import asyncio

# Import components from the simulation environment
from backend.governance.simulation.synthetic_account_modeler import SyntheticAccountGenerator, SyntheticAccount # NEW
from backend.governance.simulation.market_simulator import MarketSimulator # NEW
from backend.governance.simulation.synthetic_account_modeler import calculate_lot_size # ADD: Import calculate_lot_size
from backend.governance.simulation.synthetic_account_modeler import MoneyManagementMode  # FIX: Import MoneyManagementMode
from backend.fundamental_analysis.news_sentiment_analyzer import NewsSentimentAnalyzer  # ADD: Import NewsSentimentAnalyzer

# Default stop loss points for autonomous trading simulation
AUTONOMOUS_DEFAULT_STOP_LOSS_POINTS = 100  # You can adjust this value as needed

# Import governance components
from backend.governance.ethical_framework import EthicalScaffoldingManager, EthicalStatus, ComplianceStatus # NEW

# Import PrivAgent for conceptual agent interaction
from backend.multi_agent.priv_agent import PrivAgent # NEW
from backend.multi_agent.priv_agent_protocol import TradeProposal, TradeAction # NEW
from backend.fundamental_analysis.news_sourcing.news_api_client import NewsAPIClient  # ADD: Import NewsAPIClient
from backend.multi_agent.agent_reputation_ledger import AgentReputationLedger  # FIX: Import AgentReputationLedger

logger = logging.getLogger(__name__)

class BehavioralCalibrationEngine:
    """
    Manages the simulation-based behavioral calibration and learning for Priv Agents.
    This implements the Behavioral Feedback Loop and is central to AI calibration.
    """
    def __init__(self,
                 market_simulator: MarketSimulator,
                 account_generator: SyntheticAccountGenerator,
                 ethical_manager: EthicalScaffoldingManager,
                 target_agent: PrivAgent # The Priv Agent whose behavior is being calibrated
                ):
        """
        Initializes the BehavioralCalibrationEngine.

        Args:
            market_simulator (MarketSimulator): An instance of the MarketSimulator.
            account_generator (SyntheticAccountGenerator): An instance of the SyntheticAccountGenerator.
            ethical_manager (EthicalScaffoldingManager): An instance of the EthicalScaffoldingManager.
            target_agent (PrivAgent): The specific Priv Agent instance to be calibrated.
        """
        self.market_simulator = market_simulator
        self.account_generator = account_generator
        self.ethical_manager = ethical_manager
        self.target_agent = target_agent
        self.simulation_logs: List[Dict[str, Any]] = [] # Log of actions and outcomes in simulation
        logger.info(f"Priv's BehavioralCalibrationEngine initialized for agent '{self.target_agent.agent_id}'.")

    async def run_simulation_episode(
        self,
        sim_account_id: str,
        num_bars_to_simulate: int = 100,
        inject_shocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Runs a single simulation episode where the target Priv Agent makes decisions
        in the simulated market.

        Args:
            sim_account_id (str): The ID of the synthetic account to use for this episode.
            num_bars_to_simulate (int): Number of market bars to simulate.
            inject_shocks (Optional[List[Dict[str, Any]]]): List of shocks to inject during simulation.

        Returns:
            Dict[str, Any]: Summary of the simulation episode.
        """
        logger.info(f"Priv: Running simulation episode for agent '{self.target_agent.agent_id}' on account '{sim_account_id}'.")
        
        sim_account = self.account_generator.get_account(sim_account_id)
        if not sim_account:
            logger.error(f"Priv: Synthetic account '{sim_account_id}' not found for simulation.")
            return {"status": "failed", "reason": "Account not found."}

        self.simulation_logs = [] # Clear logs for new episode
        initial_equity = sim_account.current_equity
        
        # Schedule shocks if any
        if inject_shocks:
            for shock in inject_shocks:
                self.market_simulator.inject_shock(shock["type"], shock["at_index"], shock["params"])

        if not self.market_simulator.start_simulation():
            logger.error("Priv: Failed to start market simulation.")
            return {"status": "failed", "reason": "Simulation start failed."}

        current_bar_counter = 0
        while self.market_simulator.is_simulation_active and current_bar_counter < num_bars_to_simulate:
            current_bar = self.market_simulator.advance_bar()
            if current_bar is None:
                break # Simulation ended

            # Priv Agent's decision cycle in simulation
            # We need to simulate the environment context for StrategicAdvisor
            
            # --- Prepare mocked inputs for StrategicAdvisor ---
            # This is a simplification; in real simulation, StrategicAdvisor's methods are run fully.
            # Here, we just extract data from the current bar and mock other contexts.
            
            mock_ohlcv_data = {current_bar.name: pd.DataFrame([current_bar])} # Single bar DataFrame
            mock_symbol_info = {
                current_bar.name: {"point": 0.0001, "spread": 2, "digits": 5, "stops_level": 10, "volume_max": 100}
            } # Simplified symbol info
            mock_current_prices = {"bid": current_bar['close'] - (mock_symbol_info[current_bar.name]['point'] * mock_symbol_info[current_bar.name]['spread']), "ask": current_bar['close']} # Bid/Ask from close and spread
            mock_news_trading_status = "NORMAL_TRADING_CONDITIONS" # Assume normal news during sim for now
            mock_news_analysis_results = {"sentiment": "neutral", "market_impact": "none", "title": "No relevant news in sim."}
            
            # Update synthetic account context with current bar price
            sim_account.current_market_stress_level = self._assess_market_stress(current_bar) # Dynamically set stress
            mock_context_for_decision = {
                "account_equity": sim_account.current_equity,
                "account_free_margin": sim_account.free_margin,
                "account_drawdown": (initial_equity - sim_account.current_equity) / initial_equity if initial_equity > 0 else 0.0,
                "portfolio_total_risk_pct": 0.0, # Will be calculated by StrategicAdvisor
                "current_market_volatility": (current_bar['high'] - current_bar['low']) / current_bar['close'] if current_bar['close'] else 0.0,
                "avg_daily_volume": current_bar['volume'], # Use current bar volume as average for sim
                "contract_size": 100000,
                "news_trading_status": mock_news_trading_status,
                "llm_market_impact": mock_news_analysis_results.get('market_impact', 'none').lower(),
                "llm_news_title": mock_news_analysis_results.get('title', 'N/A')
            }

            # --- Priv Agent makes autonomous decision (via its StrategicAdvisor) ---
            # The strategic_advisor._make_autonomous_trade_decision is async.
            # We need to adapt it to return the 'proposed action' and whether it was 'executed'
            # without actually calling `execute_market_order` on a real broker.
            
            # For this simulation, we will run `_make_autonomous_trade_decision` but
            # intercept the `execute_market_order` call and just record the decision.
            
            # This requires mocking `execute_market_order` and `close_position_by_id`
            # within the scope of this simulation.
            
            # We will refactor `_make_autonomous_trade_decision` in StrategicAdvisor
            # to take an optional `simulation_mode` flag, which would prevent real execution.
            # For now, we'll assume a way to get the *proposed action* from the agent.
            
            # This part needs careful design: the `StrategicAdvisor._make_autonomous_trade_decision`
            # directly calls `execute_market_order`. For simulation, we need to bypass this.
            
            # Temporary solution: Directly call StrategicAdvisor's analytical parts
            # and simulate the decision process based on its final fuzzy signal.
            
            # Run the `analyze_market_data` which gets the fuzzy signal
            analysis_for_sim = self.target_agent.strategic_advisor.analyze_market_data(mock_ohlcv_data)
            
            # Extract the overall signal for the current symbol (assuming primary_symbol from agent init is current_bar.name)
            sim_signal_data = analysis_for_sim.get(current_bar.name, {}).get("overall_signal", {})
            sim_trade_action = sim_signal_data.get("recommendation")
            sim_signal_strength = sim_signal_data.get("strength")
            
            # Simulate arbitration and ethical/regulatory checks for the proposed action
            # This involves calling the same logic as in _make_autonomous_trade_decision.
            
            # Create a simplified TradeProposal structure for simulation
            if sim_trade_action in ["BUY", "SELL"]:
                # Calculate lot size for simulation
                sim_calculated_volume = await calculate_lot_size(
                    symbol=current_bar.name,
                    order_type=sim_trade_action,
                    money_management_amount=0.01, # Example risk
                    mm_mode=MoneyManagementMode.LOSSBALANCE,
                    account_equity=sim_account.current_equity,
                    account_free_margin=sim_account.free_margin,
                    current_prices=mock_current_prices,
                    symbol_info=mock_symbol_info[current_bar.name],
                    stop_loss_points=AUTONOMOUS_DEFAULT_STOP_LOSS_POINTS
                )
                
                if sim_calculated_volume > 0:
                    sim_trade_proposal = TradeProposal(
                        symbol=current_bar.name,
                        action=TradeAction[sim_trade_action],
                        volume=sim_calculated_volume,
                        entry_price=mock_current_prices["ask"] if sim_trade_action == "BUY" else mock_current_prices["bid"],
                        reasoning="Simulated proposal",
                        confidence=abs(sim_signal_strength)/100.0,
                        stop_loss=0.0, take_profit=0.0 # Placeholder
                    )
                    
                    # Run ethical and regulatory checks for this simulated proposal
                    regulatory_check = self.ethical_manager.check_ethical_compliance(sim_trade_proposal.model_dump(), mock_context_for_decision, self.target_agent.persona)
                    ethical_check = self.ethical_manager.check_ethical_compliance(sim_trade_proposal.model_dump(), mock_context_for_decision, self.target_agent.persona) # Using ethical manager for this
                    
                    if regulatory_check["status"] == ComplianceStatus.NON_COMPLIANT or ethical_check["status"] == EthicalStatus.NON_COMPLIANT:
                        logger.info(f"Priv: Sim decision for {current_bar.name} REJECTED due to compliance/ethics violations.")
                        sim_trade_action = "HOLD" # Override to HOLD if non-compliant
                        # Record non-compliance in reputation ledger
                        self.target_agent.strategic_advisor.agent_reputation_ledger.record_compliance_check_outcome(
                            self.target_agent.agent_id, "sim_regulatory", regulatory_check["status"].value, regulatory_check["violations"]
                        )
                        self.target_agent.strategic_advisor.agent_reputation_ledger.record_compliance_check_outcome(
                            self.target_agent.agent_id, "sim_ethical", ethical_check["status"].value, ethical_check["violations"]
                        )
                    else:
                        # Simulate execution and PnL impact
                        # For simplicity, assume PnL based on a random walk from entry to close
                        # A proper simulation would run trade outcomes over next bars.
                        simulated_pnl_on_trade = (current_bar['close'] - sim_trade_proposal.entry_price) * sim_trade_proposal.volume * 100000 # Rough estimate
                        sim_account.apply_simulated_pnl(simulated_pnl_on_trade)
                        sim_account.record_simulated_trade(sim_trade_proposal.model_dump())
                        logger.info(f"Priv: Sim decision for {current_bar.name}: {sim_trade_action} {sim_calculated_volume:.2f} PnL: {simulated_pnl_on_trade:.2f}")

                        # Record trade outcome in reputation ledger
                        self.target_agent.strategic_advisor.agent_reputation_ledger.record_trade_proposal_outcome(
                            self.target_agent.agent_id, sim_trade_proposal.model_dump(), {"action": sim_trade_action}, True # Assume approved
                        )
                else:
                    sim_trade_action = "HOLD" # If volume calc fails in sim
            else:
                sim_trade_action = "HOLD" # No strong BUY/SELL signal

            # Log simulation step
            self.simulation_logs.append({
                "bar_index": self.market_simulator.current_bar_index,
                "timestamp": current_bar.name.isoformat(),
                "agent_proposed_action": sim_trade_action,
                "agent_signal_strength": sim_signal_strength,
                "current_equity": sim_account.current_equity,
                "account_drawdown": (initial_equity - sim_account.current_equity) / initial_equity if initial_equity > 0 else 0.0,
                "market_stress": sim_account.current_market_stress_level
            })
            current_bar_counter += 1

        final_equity = sim_account.current_equity
        final_pnl_pct = (final_equity - initial_equity) / initial_equity if initial_equity > 0 else 0.0
        
        logger.info(f"Priv: Simulation episode finished. Final Equity: {final_equity:.2f} ({final_pnl_pct:.2%}).")
        
        # Calibration step after episode (Conceptual)
        self.calibrate_agent_behavior(self.target_agent, final_pnl_pct, sim_account.current_market_stress_level)

        return {
            "status": "completed",
            "initial_equity": initial_equity,
            "final_equity": final_equity,
            "total_pnl_pct": final_pnl_pct,
            "num_bars_simulated": current_bar_counter,
            "simulated_logs": self.simulation_logs
        }
    
    def _assess_market_stress(self, current_bar: pd.Series) -> float:
        """Heuristically assesses market stress from bar data (e.g., high volatility)."""
        # A simple proxy: larger range relative to close, or presence of flash crash shocks
        range_pct = (current_bar['high'] - current_bar['low']) / current_bar['close'] if current_bar['close'] else 0.0
        # Scale to 0-1.0
        if range_pct > 0.02: return 1.0 # Very high volatility
        if range_pct > 0.01: return 0.7 # High volatility
        return 0.3 # Low/medium volatility

    def calibrate_agent_behavior(self, agent: PrivAgent, episode_pnl_pct: float, avg_market_stress: float):
        """
        Conceptually calibrates the Priv Agent's behavior based on simulation results.
        This is where Reinforcement Learning (RL) agents would adjust policies.
        """
        logger.info(f"Priv: Calibrating agent '{agent.agent_id}' based on sim PnL: {episode_pnl_pct:.2%} and avg stress: {avg_market_stress:.2f}.")
        
        # Example conceptual RL feedback loop:
        # If model performed well in high stress, reinforce that behavior.
        # If model lost money and persona was aggressive, suggest reducing aggression.

        # 1. Evaluate behavior against ethical principles (already done in simulation, but for overall episode)
        # This is for the overall episode performance, not just single trades.
        # Check against "Behavioral Feedback Loop" in patent
        
        # 2. Adjust persona attributes (Dynamic Persona Synthesis)
        # This is a key part of dynamic persona synthesis
        
        # Example: If simulation resulted in significant loss and agent's risk tolerance was 'high'
        if episode_pnl_pct < -0.02 and agent.persona.get("risk_tolerance") == "high": # More than 2% loss
            agent.persona["risk_tolerance"] = "medium" # Reduce risk tolerance
            logger.warning(f"Priv: Agent '{agent.agent_id}' risk tolerance adjusted to 'medium' due to simulation loss.")
            # Record this adjustment in the Reputation Ledger, possibly as a 'human_override' or 'self_calibration'
        
        elif episode_pnl_pct > 0.05 and agent.persona.get("risk_tolerance") == "medium": # Significant profit
            agent.persona["risk_tolerance"] = "high" # Increase risk tolerance if successful
            logger.info(f"Priv: Agent '{agent.agent_id}' risk tolerance adjusted to 'high' due to simulation profit.")

        # 3. Update internal strategy parameters (conceptual for RL agents)
        # This would be where an RL agent updates its Q-values or policy network weights.
        # For our current fuzzy/rule-based advisor, this implies adjusting fuzzy rules or thresholds.
        # `agent.strategic_advisor.fuzzy_controller._setup_fuzzy_system()` could be re-called with new params.
        
        # Example: If MarketIntegrityPrinciple was violated frequently, slightly adjust fuzzy inputs
        # or strategy rules to prioritize smaller volumes.
        
        logger.info(f"Priv: Calibration complete for agent '{agent.agent_id}'. New persona (risk_tolerance): {agent.persona['risk_tolerance']}")


# Example Usage (for testing BehavioralCalibrationEngine in isolation)
async def main_behavioral_calibration_test():
    logging.basicConfig(level=logging.INFO)

    # --- Setup Dependencies ---
    # Mock Historical Data
    data_length = 300
    dates = pd.date_range(start='2023-01-01', periods=data_length, freq='D')
    mock_closes = 100 + np.cumsum(np.random.normal(0, 0.5, data_length))
    mock_opens = mock_closes - np.random.uniform(-0.1, 0.1, data_length)
    mock_highs = np.maximum(mock_opens, mock_closes) + np.random.uniform(0, 0.2, data_length)
    mock_lows = np.minimum(mock_opens, mock_closes) - np.random.uniform(0, 0.2, data_length)
    mock_volumes = np.random.randint(1000, 5000, data_length)
    mock_df = pd.DataFrame({'open': mock_opens, 'high': mock_highs, 'low': mock_lows, 'close': mock_closes, 'volume': mock_volumes}, index=dates)
    mock_df.index.name = 'timestamp'

    # Initialize Simulator, Account Generator, Ethical Manager
    market_simulator = MarketSimulator(historical_data=mock_df)
    account_generator = SyntheticAccountGenerator()
    ethical_manager = EthicalScaffoldingManager(principles_definitions_path="backend/governance/ethical_principles.json")
    # For testing, ensure mock ethical_principles.json exists as in its `if __name__ == '__main__':`
    # You would need to run that example's main or manually create the file.
    # For a clean test, ensure the file is created:
    mock_principles_content = [
        {
            "principle_id": "CP_HighDrawdown", "name": "Capital Preservation", "description": "High drawdown",
            "category": "risk_management", "severity": "critical", "parameters": {"max_drawdown_percent": 0.05, "risk_tolerance_threshold": "medium"},
            "check_function_name": "CapitalPreservationPrinciple"
        }
    ]
    if not os.path.exists("backend/governance/ethical_principles.json"):
        os.makedirs("backend/governance", exist_ok=True)
        with open("backend/governance/ethical_principles.json", "w") as f:
            json.dump(mock_principles_content, f)
        ethical_manager = EthicalScaffoldingManager(principles_definitions_path="backend/governance/ethical_principles.json")

    # Initialize a Priv Agent for calibration
    # Note: This PrivAgent's StrategicAdvisor needs proper mocks or a full instance for its analysis to run.
    # For this isolated test, we'll create a dummy StrategicAdvisor for the PrivAgent.
    
    class DummyStrategicAdvisorForSim:
        def __init__(self, *args, **kwargs):
            self.fuzzy_controller = lambda: None # Mock to avoid error
            self.agent_reputation_ledger = AgentReputationLedger(ledger_filepath="temp_reputation_ledger_sim_test.jsonl")
            self.news_api_client = NewsAPIClient(use_mock=True) # Mock news client
            self.news_sentiment_analyzer = NewsSentimentAnalyzer(openai_api_key="mock_key") # Mock sentiment
        def analyze_market_data(self, ohlcv_data):
            # Simulate returning analysis_results with a fuzzy signal
            if ohlcv_data:
                latest_close = list(ohlcv_data.values())[0]['close'].iloc[-1]
                # Simulate a bullish signal if price goes up, bearish if down
                if latest_close > 105:
                    return {list(ohlcv_data.keys())[0]: {"overall_signal": {"recommendation": "BUY", "strength": 80.0, "directional_confirmations_score": 4}, "latest_standard_indicators": {'rsi': 25.0, 'macd_hist': 1.0}}}
                elif latest_close < 95:
                    return {list(ohlcv_data.keys())[0]: {"overall_signal": {"recommendation": "SELL", "strength": -80.0, "directional_confirmations_score": -4}, "latest_standard_indicators": {'rsi': 75.0, 'macd_hist': -1.0}}}
                else:
                    return {list(ohlcv_data.keys())[0]: {"overall_signal": {"recommendation": "HOLD", "strength": 0.0, "directional_confirmations_score": 0}, "latest_standard_indicators": {'rsi': 50.0, 'macd_hist': 0.0}}}
            return {}
        def _get_fuzzy_controller_inputs(self, analysis_results_for_symbol, news_analysis_results, news_trading_status):
            return {"momentum_score": 50.0, "pattern_confirmation": 50.0, "news_impact": 0.0, "confirmation_count": 5.0} # Mock inputs
        def fuzzy_controller(self): # Mock fuzzy_controller for get_signal/get_trading_recommendation
            return lambda: None # Placeholder, actual usage is mocked in `analyze_market_data` for sim
            
        async def _make_autonomous_trade_decision(self, *args, **kwargs):
            # This is the method we are trying to simulate behavior *of*.
            # In real calibration, this method *would* be called.
            # For this test, we are evaluating the *output* of `analyze_market_data` and simulating trade.
            pass
        
    class MockPrivAgentSim(PrivAgent):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.strategic_advisor = DummyStrategicAdvisorForSim() # Inject dummy advisor

    agent_calibrated = MockPrivAgentSim(agent_id="Priv-Calibrating", persona={"name": "Learning Priv", "risk_tolerance": "medium"})
    
    calibration_engine = BehavioralCalibrationEngine(
        market_simulator=market_simulator,
        account_generator=account_generator,
        ethical_manager=ethical_manager,
        target_agent=agent_calibrated
    )

    # Create a synthetic account for the simulation
    sim_account_test = account_generator.create_account(initial_equity=50000.0, account_id="TestSimAccount")

    print("\n--- Running Simulation Episode 1 (No Shocks) ---")
    episode_summary = await calibration_engine.run_simulation_episode(
        sim_account_id="TestSimAccount",
        num_bars_to_simulate=150
    )
    print(f"Episode Summary 1: {episode_summary}")
    print(f"Agent's persona after sim 1 (risk_tolerance): {agent_calibrated.persona['risk_tolerance']}")


    print("\n--- Running Simulation Episode 2 (With Flash Crash and High Drawdown) ---")
    # Reset account state for new episode, or create a new account
    sim_account_test_2 = account_generator.create_account(initial_equity=50000.0, risk_appetite=0.6, account_id="TestSimAccount2")
    
    # Inject a flash crash early in the simulation
    shocks_for_episode2 = [
        {"type": "flash_crash", "at_index": 30, "params": {"magnitude": 0.07}} # 7% crash
    ]
    
    # Ensure ethical manager has principles activated for the agent's persona
    ethical_manager.activate_principles_for_persona(agent_calibrated.persona)

    episode_summary_2 = await calibration_engine.run_simulation_episode(
        sim_account_id="TestSimAccount2",
        num_bars_to_simulate=150,
        inject_shocks=shocks_for_episode2
    )
    print(f"Episode Summary 2: {episode_summary_2}")
    print(f"Agent's persona after sim 2 (risk_tolerance): {agent_calibrated.persona['risk_tolerance']}")
    
    # Clean up mock files
    if os.path.exists("backend/governance/ethical_principles.json"):
        os.remove("backend/governance/ethical_principles.json")
    if os.path.exists("temp_reputation_ledger_sim_test.jsonl"):
        os.remove("temp_reputation_ledger_sim_test.jsonl")
    logger.info("Cleaned up mock files.")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main_behavioral_calibration_test())