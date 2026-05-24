"""
Example Agent Implementations using the new Pub/Sub system
These demonstrate the recommended pattern for writing PRIV agents
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.communication import Agent

logger = logging.getLogger(__name__)


class StrategistAgent(Agent):
    """
    Strategist Agent - Generates trading strategies and proposals
    Example of a proper Agent implementation using Pub/Sub
    """
    
    def __init__(self, agent_id: str = "strategist-001"):
        super().__init__(
            agent_id=agent_id,
            agent_type="strategist",
            topics=["agent.strategist", "workflow.trade"]
        )
        self.market_sentiment = {}
        self.latest_prices = {}
    
    async def _initialize(self) -> None:
        """Initialize strategist agent"""
        logger.info(f"{self.agent_id}: Initializing strategist agent")
        # Load any models, data, or configuration
        self.market_sentiment = {"overall": "neutral"}
    
    async def _cleanup(self) -> None:
        """Clean up strategist agent"""
        logger.info(f"{self.agent_id}: Cleaning up")
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming messages"""
        action = message.get("action")
        
        if action == "generate_proposal":
            return await self.handle_proposal_request(message)
        elif action == "update_sentiment":
            await self.handle_sentiment_update(message)
        elif action == "market_data":
            await self.handle_market_data(message)
        
        return None
    
    async def handle_proposal_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a proposal generation request"""
        symbol = request.get("symbol")
        logger.info(f"{self.agent_id}: Generating proposal for {symbol}")
        
        # Get latest price
        price = self.latest_prices.get(symbol, 100.0)
        
        # Generate proposal based on sentiment
        sentiment = self.market_sentiment.get("overall", "neutral")
        action = "BUY" if sentiment == "positive" else "SELL" if sentiment == "negative" else "HOLD"
        
        proposal = {
            "proposal_id": f"prop-{datetime.utcnow().timestamp()}",
            "symbol": symbol,
            "action": action,
            "entry_price": price,
            "confidence": 0.75,
            "reasoning": f"Generated proposal based on {sentiment} sentiment"
        }
        
        # Log activity
        await self.log_activity("proposal_generated", proposal)
        
        return proposal
    
    async def handle_sentiment_update(self, message: Dict[str, Any]) -> None:
        """Update market sentiment from news agents"""
        sentiment = message.get("sentiment", "neutral")
        source = message.get("source", "unknown")
        logger.info(f"{self.agent_id}: Sentiment update from {source}: {sentiment}")
        self.market_sentiment = {
            "overall": sentiment,
            "source": source,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def handle_market_data(self, message: Dict[str, Any]) -> None:
        """Update prices from market data agents"""
        symbol = message.get("symbol")
        price = message.get("price")
        if symbol and price:
            self.latest_prices[symbol] = price
            logger.debug(f"{self.agent_id}: Updated {symbol} = {price}")


class RiskAgent(Agent):
    """
    Risk Agent - Analyzes risk and validates proposals
    Example of an agent that processes requests and sends responses
    """
    
    def __init__(self, agent_id: str = "risk-001"):
        super().__init__(
            agent_id=agent_id,
            agent_type="risk",
            topics=["agent.risk", "workflow.trade"]
        )
        self.portfolio = {}
        self.max_single_position_pct = 0.05
    
    async def _initialize(self) -> None:
        """Initialize risk agent"""
        logger.info(f"{self.agent_id}: Initializing risk agent")
        self.portfolio = {"total_value": 100000.0, "positions": {}}
    
    async def _cleanup(self) -> None:
        """Clean up risk agent"""
        logger.info(f"{self.agent_id}: Cleaning up")
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming messages"""
        action = message.get("action")
        
        if action == "analyze_proposal":
            return await self.analyze_proposal(message)
        elif action == "analyze_risk":
            return await self.analyze_risk(message)
        
        return None
    
    async def analyze_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a proposal for risk"""
        symbol = proposal.get("symbol")
        action = proposal.get("action")
        logger.info(f"{self.agent_id}: Analyzing risk for {symbol}")
        
        # Check position size
        entry_price = proposal.get("entry_price", 100.0)
        proposed_notional = entry_price * 100  # Assume 100 shares
        position_pct = proposed_notional / self.portfolio["total_value"]
        
        # Assess risk
        risk_level = "LOW"
        approved = True
        
        if position_pct > self.max_single_position_pct:
            risk_level = "HIGH"
            approved = False
        elif position_pct > self.max_single_position_pct * 0.5:
            risk_level = "MEDIUM"
        
        analysis = {
            "proposal_id": proposal.get("proposal_id"),
            "symbol": symbol,
            "risk_level": risk_level,
            "approved": approved,
            "position_pct": position_pct,
            "max_allowed_pct": self.max_single_position_pct
        }
        
        await self.log_activity("risk_analysis", analysis)
        return analysis
    
    async def analyze_risk(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio risk"""
        symbols = request.get("symbols", [])
        logger.info(f"{self.agent_id}: Analyzing portfolio risk for {len(symbols)} symbols")
        
        return {
            "portfolio_risk_score": 45.0,  # 0-100
            "var_95": 5000.0,  # Value at risk
            "symbols_analyzed": len(symbols),
            "recommendations": ["Reduce concentration", "Hedge downside"]
        }


class ExecutionAgent(Agent):
    """
    Execution Agent - Executes approved trades
    Example of an agent that executes actions and reports results
    """
    
    def __init__(self, agent_id: str = "execution-001"):
        super().__init__(
            agent_id=agent_id,
            agent_type="execution",
            topics=["agent.execution", "workflow.trade"]
        )
        self.executed_trades = []
    
    async def _initialize(self) -> None:
        """Initialize execution agent"""
        logger.info(f"{self.agent_id}: Initializing execution agent")
    
    async def _cleanup(self) -> None:
        """Clean up execution agent"""
        logger.info(f"{self.agent_id}: Cleaning up")
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming messages"""
        action = message.get("action")
        
        if action == "execute_trade":
            return await self.execute_trade(message)
        elif action == "get_execution_history":
            return {"executed_trades": self.executed_trades}
        
        return None
    
    async def execute_trade(self, trade_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trade"""
        symbol = trade_request.get("symbol")
        action = trade_request.get("action")
        entry_price = trade_request.get("entry_price", 100.0)
        
        logger.info(f"{self.agent_id}: Executing {action} trade for {symbol} at {entry_price}")
        
        # Simulate trade execution
        trade_result = {
            "trade_id": f"trade-{datetime.utcnow().timestamp()}",
            "symbol": symbol,
            "action": action,
            "executed_price": entry_price * (1.0 + (0.001 if action == "BUY" else -0.001)),
            "quantity": 100,
            "status": "EXECUTED",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.executed_trades.append(trade_result)
        
        await self.log_activity("trade_executed", trade_result)
        return trade_result


class NewsAnalysisAgent(Agent):
    """
    News Analysis Agent - Analyzes news and extracts sentiment
    Example of an agent that publishes results to other agents
    """
    
    def __init__(self, agent_id: str = "news-001"):
        super().__init__(
            agent_id=agent_id,
            agent_type="news_analysis",
            topics=["agent.news_analysis", "workflow.news"]
        )
        self.sentiment_keywords = {
            "positive": ["surge", "gain", "rally", "soars", "excellent"],
            "negative": ["crash", "plunge", "fall", "weak", "decline"],
        }
    
    async def _initialize(self) -> None:
        """Initialize news analysis agent"""
        logger.info(f"{self.agent_id}: Initializing news analysis agent")
    
    async def _cleanup(self) -> None:
        """Clean up news analysis agent"""
        logger.info(f"{self.agent_id}: Cleaning up")
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process incoming messages"""
        action = message.get("action")
        
        if action == "analyze_news":
            return await self.analyze_news(message)
        
        return None
    
    async def analyze_news(self, news_request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a news article"""
        headline = news_request.get("headline", "")
        content = news_request.get("content", "")
        
        # Determine sentiment
        text = (headline + " " + content).lower()
        sentiment = "neutral"
        
        for keyword in self.sentiment_keywords["positive"]:
            if keyword in text:
                sentiment = "positive"
                break
        
        for keyword in self.sentiment_keywords["negative"]:
            if keyword in text:
                sentiment = "negative"
                break
        
        analysis = {
            "sentiment": sentiment,
            "headline": headline,
            "confidence": 0.8,
            "impact": "high" if len(content) > 500 else "medium"
        }
        
        # Publish sentiment update to strategist
        await self.publish_message("agent.strategist", {
            "action": "update_sentiment",
            "sentiment": sentiment,
            "source": self.agent_id
        })
        
        await self.log_activity("news_analyzed", analysis)
        return analysis


# Convenience function to create all example agents
def create_example_agents() -> list:
    """Create all example agents"""
    return [
        StrategistAgent(),
        RiskAgent(),
        ExecutionAgent(),
        NewsAnalysisAgent(),
    ]
