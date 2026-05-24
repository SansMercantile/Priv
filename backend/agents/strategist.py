"""
priv/backend/agents/strategist.py
Strategist Agent - Analyzes market data and generates trading signals

Subscribes to: priv-market-data
Publishes to: priv-trade-signals
State stored in: firestore/agents/strategist/
"""

import os
import sys
import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class StrategistAgent(BaseAgent):
    """
    The Strategist Agent analyzes market data and generates trading signals.

    Process:
    1. Receives market data (price, volume, indicators)
    2. Runs technical analysis
    3. Evaluates market sentiment
    4. Generates buy/sell/hold signals with confidence scores
    5. Publishes signals to priv-trade-signals topic
    """

    def __init__(self):
        super().__init__(
            agent_name="strategist",
            subscription_ids=["strategist-market-data"],
            output_topic="priv-trade-signals"
        )
        self.min_confidence = 0.7  # Only signal if confidence >= 70%

    async def process_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process market data and generate trading signal.

        Input message format:
        {
            "symbol": "AAPL",
            "price": 150.25,
            "volume": 1000000,
            "bid": 150.24,
            "ask": 150.26,
            "timestamp": "2025-12-26T14:30:00Z",
            "indicators": {
                "rsi": 45.5,
                "macd": 0.15,
                "momentum": "bullish",
                "bollinger_position": 0.65,
                "ema_signal": "above"
            }
        }

        Output signal format:
        {
            "signal_id": "sig_12345",
            "timestamp": "2025-12-26T14:30:00Z",
            "symbol": "AAPL",
            "action": "BUY",  # BUY, SELL, HOLD
            "quantity": 100,
            "confidence": 0.85,
            "reasoning": "Golden cross detected + RSI recovery",
            "indicators_used": [...],
            "agent_id": "strategist_001"
        }
        """

        try:
            symbol = message_data.get('symbol')
            price = message_data.get('price')
            indicators = message_data.get('indicators', {})

            logger.info(f"[STRATEGIST] Analyzing {symbol} @ ${price}")

            # Step 1: Technical analysis
            signal, confidence, reasoning = await self.analyze_technicals(
                symbol, price, indicators
            )

            # Step 2: Sentiment analysis
            sentiment_boost = await self.get_sentiment_boost(symbol)
            confidence = min(confidence * sentiment_boost, 1.0)

            # Step 3: Risk assessment
            is_safe = await self.check_market_conditions(symbol, price)
            if not is_safe:
                signal = "HOLD"
                confidence *= 0.5

            # Step 4: Generate signal if confidence sufficient
            result = None
            if confidence >= self.min_confidence:
                result = await self.generate_signal(
                    symbol=symbol,
                    action=signal,
                    price=price,
                    confidence=confidence,
                    reasoning=reasoning,
                    indicators=indicators
                )

                logger.info(
                    f"[STRATEGIST] Signal generated: {symbol} {signal} "
                    f"(confidence: {confidence:.2%})"
                )

            return result

        except Exception as e:
            logger.error(f"[STRATEGIST] Error analyzing market data: {str(e)}")
            return None

    async def analyze_technicals(
        self,
        symbol: str,
        price: float,
        indicators: Dict[str, Any]
    ) -> tuple:
        """
        Analyze technical indicators to generate signal.

        Returns:
            (signal, confidence, reasoning) - (str, float, str)
        """

        signal = "HOLD"
        confidence = 0.5
        reasoning_parts = []

        # RSI Analysis (0-100, <30 oversold, >70 overbought)
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            signal = "BUY"
            confidence += 0.2
            reasoning_parts.append(f"RSI oversold ({rsi})")
        elif rsi > 70:
            signal = "SELL"
            confidence += 0.15
            reasoning_parts.append(f"RSI overbought ({rsi})")

        # MACD Analysis (momentum)
        macd = indicators.get('macd', 0)
        if macd > 0.1:
            signal = "BUY"
            confidence += 0.15
            reasoning_parts.append("MACD positive crossover")
        elif macd < -0.1:
            signal = "SELL"
            confidence += 0.15
            reasoning_parts.append("MACD negative crossover")

        # Bollinger Bands Position (0-1, closer to 1 = upper band)
        bb_pos = indicators.get('bollinger_position', 0.5)
        if bb_pos > 0.8:
            signal = "SELL"
            confidence += 0.1
            reasoning_parts.append("Price near upper Bollinger Band")
        elif bb_pos < 0.2:
            signal = "BUY"
            confidence += 0.1
            reasoning_parts.append("Price near lower Bollinger Band")

        # EMA Signal
        ema_signal = indicators.get('ema_signal', 'neutral')
        if ema_signal == 'above':
            signal = "BUY"
            confidence += 0.1
            reasoning_parts.append("Price above EMA")
        elif ema_signal == 'below':
            signal = "SELL"
            confidence += 0.1
            reasoning_parts.append("Price below EMA")

        # Momentum
        momentum = indicators.get('momentum', 'neutral')
        if momentum == 'bullish':
            signal = "BUY"
            confidence += 0.05
        elif momentum == 'bearish':
            signal = "SELL"
            confidence += 0.05

        # Normalize confidence
        confidence = min(max(confidence, 0.0), 1.0)
        reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Neutral market"

        return signal, confidence, reasoning

    async def get_sentiment_boost(self, symbol: str) -> float:
        """
        Get sentiment score from Firestore and apply as multiplier.
        Returns 0.7-1.3 multiplier on confidence.
        """
        try:
            sentiment_doc = self.db.collection('market_cache').document(
                f'sentiment_{symbol}'
            ).get()

            if sentiment_doc.exists:
                sentiment_score = sentiment_doc.get('sentiment_score', 0.5)
                # Convert [-1, 1] sentiment to [0.7, 1.3] multiplier
                multiplier = 1.0 + (sentiment_score * 0.3)
                return max(multiplier, 0.7)

        except Exception as e:
            logger.debug(f"Could not fetch sentiment for {symbol}: {str(e)}")

        return 1.0  # Neutral if not available

    async def check_market_conditions(self, symbol: str, price: float) -> bool:
        """
        Check if market conditions are safe for trading.
        Prevents trading during extreme volatility, market halts, etc.

        Returns:
            True if safe to trade, False otherwise
        """
        try:
            # Check for circuit breakers (if VIX too high)
            vix_doc = self.db.collection('market_cache').document('vix').get()
            if vix_doc.exists:
                vix = vix_doc.get('value', 20)
                if vix > 40:  # Very high volatility
                    logger.warning(f"High VIX ({vix}), reducing trade confidence")
                    return False

            # Check for trading halts
            halt_doc = self.db.collection('market_cache').document(
                f'halt_{symbol}'
            ).get()
            if halt_doc.exists and halt_doc.get('is_halted', False):
                logger.warning(f"{symbol} is halted")
                return False

            return True

        except Exception as e:
            logger.debug(f"Could not check market conditions: {str(e)}")
            return True  # Assume safe if check fails

    async def generate_signal(
        self,
        symbol: str,
        action: str,
        price: float,
        confidence: float,
        reasoning: str,
        indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a trading signal message.
        """

        # Calculate quantity based on confidence (Kelly Criterion)
        # Conservative: quantity = floor(confidence * 10) * 10 shares
        quantity = max(10, int(confidence * 100) // 10 * 10)

        signal = {
            "signal_id": f"sig_{datetime.utcnow().timestamp()}",
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "confidence": confidence,
            "reasoning": reasoning,
            "indicators_used": list(indicators.keys()),
            "agent_id": self.agent_name,
            "current_price": price
        }

        # Store signal in Firestore for audit trail
        try:
            signals_ref = self.db.collection('agents').document(
                self.agent_name
            ).collection('signals').document(signal['signal_id'])
            signals_ref.set({
                'timestamp': datetime.utcnow(),
                'data': signal
            })
        except Exception as e:
            logger.debug(f"Could not store signal in Firestore: {str(e)}")

        return signal


# ============================================================================
# Cloud Run Execution
# ============================================================================

async def main():
    """Entry point for Cloud Run deployment."""
    agent = StrategistAgent()
    await agent.run()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run agent
    asyncio.run(main())
