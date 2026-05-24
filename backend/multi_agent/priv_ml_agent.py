# backend/multi_agent/priv_ml_agent.py

import logging
from typing import Dict, Any, Optional
import pandas as pd
from .priv_agent import PrivAgent
from .priv_agent_protocol import TradeProposal, TradeAction, AgentType

# Make ai_core optional - it may not exist yet
try:
    from shared_resources.ai_core.feature_store import FeatureStore
    FEATURE_STORE_AVAILABLE = True
except ImportError:
    FEATURE_STORE_AVAILABLE = False
    FeatureStore = None
    logger = logging.getLogger(__name__)
    logger.warning("Feature Store not available. ML Agent will use basic features.")

from .message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivMLAgent(PrivAgent):
    """
    A specialized agent that uses machine learning models to generate trade proposals.
    It consumes feature-enriched data from the Feature Store.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.ML, message_broker=message_broker, broker=broker, persona=persona)
        self.feature_store = FeatureStore()
        self.model = self._load_model() # Load a pre-trained ML model

    def _load_model(self):
        """Placeholder for loading a trained ML model (e.g., from a .pkl file)."""
        logger.info(f"ML Agent '{self.agent_id}': Loading predictive model...")
        # import joblib
        # return joblib.load("path/to/your/model.pkl")
        return "mock_ml_model"

    async def start(self):
        if self.is_running: return
        self.is_running = True
        logger.info(f"PrivMLAgent '{self.agent_id}' started.")

    async def stop(self):
        self.is_running = False
        logger.info(f"PrivMLAgent '{self.agent_id}' stopped.")

    async def generate_trade_proposal(self, symbol: str, timeframe: str = "D1") -> Optional[TradeProposal]:
        """Generates a proposal based on the ML model's prediction."""
        features_df = self.feature_store.load_features(symbol, timeframe)
        if features_df is None or features_df.empty:
            logger.warning(f"ML Agent: No feature data available for {symbol}/{timeframe}.")
            return None

        # Get the latest feature set
        latest_features = features_df.iloc[-1:]

        # In a real system, you would preprocess features and predict
        # prediction = self.model.predict(latest_features)
        # probability = self.model.predict_proba(latest_features)
        
        # Mock prediction
        prediction = 1 # (1 for BUY, -1 for SELL, 0 for HOLD)
        probability = 0.88

        if prediction == 0:
            return None

        action = TradeAction.BUY if prediction == 1 else TradeAction.SELL
        
        return TradeProposal(
            agent_id=self.agent_id,
            symbol=symbol,
            action=action,
            volume=0.2,
            reasoning=f"ML model prediction with {probability:.2%} confidence.",
            confidence=probability,
            risk_assessment={"strategy": "ml_prediction_v1.2"}
        )
