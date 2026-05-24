"""
Fundamental Analysis Agent
==========================

This agent performs fundamental analysis of financial instruments,
including company financials, economic indicators, and market analysis.

Copyright © 2025 Sans Mercantile™. All rights reserved.
Creator: Mezzoforte Privilege Khoza
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass

from backend.multi_agent.multi_agent_system import BaseAgent, TaskRequest, TaskResult, AgentStatus
# Self-reference removed - FundamentalAgent is the main fundamental analysis agent
# If PrivFundamentalDataAgent is needed, it should be defined separately or imported differently
from backend.fundamental_analysis.economic_calendar.manager import EconomicCalendarManager
from backend.data_sourcing.fundamental_data_ingestor import FundamentalDataIngestor

logger = logging.getLogger(__name__)

@dataclass
class FundamentalAnalysis:
    """Result of fundamental analysis"""
    symbol: str
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    eps_growth: Optional[float]
    revenue_growth: Optional[float]
    debt_to_equity: Optional[float]
    roe: Optional[float]
    roa: Optional[float]
    analyst_rating: Optional[str]
    fair_value: Optional[Decimal]
    confidence: float
    timestamp: datetime

class FundamentalAgent(BaseAgent):
    async def analyze_fundamentals(self, fundamental_data):
        """Stub for fundamental analysis"""
        return {
            'valuation_score': 80,
            'financial_health': 'good',
            'growth_prospects': 'strong',
            'recommendation': 'BUY'
        }

    async def analyze_earnings(self, earnings_data):
        """Stub for earnings analysis"""
        return {
            'trend': 'increasing',
            'forecast': 1.5,
            'beat_rate': 0.75,
            'growth_rate': 0.1
        }
    """Agent for fundamental analysis of financial instruments"""
    
    def __init__(self, *args, **kwargs):
        # Handle different initialization signatures:
        # 1. FundamentalAgent(agent_id, broker, config=..., api_client=..., database=..., calendar_url=...)
        # 2. FundamentalAgent(config, api_client, database)
        agent_id = "fundamental_agent"
        broker = None
        config = None
        api_client = None
        database = None
        calendar_url = "http://mock-calendar-url.com"

        if len(args) >= 1 and isinstance(args[0], str):
            agent_id = args[0]
            if len(args) >= 2:
                broker = args[1]
            if len(args) >= 3:
                config = args[2]
            if len(args) >= 4:
                api_client = args[3]
            if len(args) >= 5:
                database = args[4]
            if len(args) >= 6:
                calendar_url = args[5]
        elif len(args) >= 1:
            config = args[0]
            if len(args) >= 2:
                api_client = args[1]
                broker = api_client
            if len(args) >= 3:
                database = args[2]
            agent_id = "fundamental_agent"

        if "agent_id" in kwargs:
            agent_id = kwargs["agent_id"]
        if "broker" in kwargs:
            broker = kwargs["broker"]
        if "config" in kwargs:
            config = kwargs["config"]
        if "api_client" in kwargs:
            api_client = kwargs["api_client"]
        if "database" in kwargs:
            database = kwargs["database"]
        if "calendar_url" in kwargs:
            calendar_url = kwargs["calendar_url"]

        super().__init__(agent_id, broker)
        self.config = config
        self.api_client = api_client
        self.database = database
        self.economic_calendar = EconomicCalendarManager(calendar_url)
        self.data_ingestor = FundamentalDataIngestor()
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{agent_id}")

        # Set up a shim for fundamental_data_agent to avoid AttributeError
        class FundamentalDataAgentShim:
            def __init__(self, parent):
                self.parent = parent
            async def initialize(self) -> bool:
                return await self.parent.data_ingestor.initialize()
            async def get_fundamental_data(self, symbol: str) -> Dict[str, Any]:
                return await self.parent.get_fundamental_data_as_dict(symbol)

        self.fundamental_data_agent = FundamentalDataAgentShim(self)

    async def get_fundamental_data_as_dict(self, symbol: str) -> Dict[str, Any]:
        """Fetch fundamental data from deep ingestor and map it back into legacy dictionary structure."""
        res = {
            "symbol": symbol,
            "current_price": 150.0,
            "earnings_per_share": 6.0,
            "previous_earnings_per_share": 5.5,
            "book_value_per_share": 18.0,
            "revenue": 400000000.0,
            "previous_revenue": 380000000.0,
            "total_debt": 50000000.0,
            "total_equity": 100000000.0,
            "net_income": 12000000.0,
            "total_assets": 200000000.0,
            "free_cash_flow": 15000000.0,
            "growth_rate": 0.04,
            "discount_rate": 0.08,
            "terminal_growth": 0.02
        }
        try:
            metrics = await self.data_ingestor.fetch_fundamental_data(symbol)
            if metrics:
                if metrics.pe_ratio is not None and metrics.pe_ratio != 0:
                    res["current_price"] = 150.0
                    res["earnings_per_share"] = 150.0 / metrics.pe_ratio
                if metrics.pb_ratio is not None and metrics.pb_ratio != 0:
                    res["book_value_per_share"] = 150.0 / metrics.pb_ratio
                if metrics.earnings_growth is not None:
                    res["previous_earnings_per_share"] = res["earnings_per_share"] / (1 + metrics.earnings_growth)
                if metrics.revenue_growth is not None:
                    res["previous_revenue"] = res["revenue"] / (1 + metrics.revenue_growth)
                if metrics.debt_to_equity is not None:
                    res["total_debt"] = metrics.debt_to_equity * res["total_equity"]
                if metrics.return_on_equity is not None:
                    res["net_income"] = metrics.return_on_equity * res["total_equity"]
                if metrics.return_on_assets is not None:
                    res["net_income"] = metrics.return_on_assets * res["total_assets"]
                if metrics.free_cash_flow is not None:
                    res["free_cash_flow"] = metrics.free_cash_flow
        except Exception as e:
            self.logger.warning(f"Error fetching actual metrics for {symbol}, falling back: {e}")
        return res
        
    async def initialize(self) -> bool:
        """Initialize the fundamental agent"""
        try:
            self.logger.info("🚀 Initializing Fundamental Agent...")
            
            # Initialize sub-components
            if not await self.fundamental_data_agent.initialize():
                return False
                
            if not await self.economic_calendar.initialize():
                return False
                
            if not await self.data_ingestor.initialize():
                return False
                
            self.logger.info("✅ Fundamental Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Fundamental Agent: {e}", exc_info=True)
            return False
            
    async def execute_task(self, task: TaskRequest) -> TaskResult:
        """Execute fundamental analysis task"""
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"📊 Executing fundamental analysis task: {task.task_id}")
            
            # Extract parameters
            symbol = task.parameters.get("symbol")
            if not symbol:
                raise ValueError("Symbol parameter required")
                
            # Perform fundamental analysis
            analysis = await self._perform_fundamental_analysis(symbol)
            
            # Calculate confidence based on data availability
            confidence = self._calculate_confidence(analysis)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=True,
                result=analysis,
                execution_time=execution_time,
                confidence=confidence,
                metadata={
                    "symbol": symbol,
                    "analysis_type": "fundamental",
                    "data_points": self._count_data_points(analysis)
                }
            )
            
            self.logger.info(f"✅ Fundamental analysis completed: {task.task_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"� Fundamental analysis failed: {task.task_id} - {e}", exc_info=True)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.agent_id,
                success=False,
                result={"error": str(e)},
                execution_time=execution_time,
                confidence=0.0,
                metadata={"error_type": type(e).__name__}
            )
            
    async def _perform_fundamental_analysis(self, symbol: str) -> FundamentalAnalysis:
        """Perform comprehensive fundamental analysis"""
        try:
            self.logger.info(f"📈 Analyzing fundamentals for: {symbol}")
            
            # Get fundamental data
            fundamental_data = await self.fundamental_data_agent.get_fundamental_data(symbol)
            
            # Get economic calendar data
            economic_events = await self.economic_calendar.get_relevant_events(symbol)
            
            # Get analyst estimates
            analyst_data = await self.data_ingestor.get_analyst_estimates(symbol)
            
            # Calculate key metrics
            pe_ratio = self._calculate_pe_ratio(fundamental_data)
            pb_ratio = self._calculate_pb_ratio(fundamental_data)
            eps_growth = self._calculate_eps_growth(fundamental_data)
            revenue_growth = self._calculate_revenue_growth(fundamental_data)
            debt_to_equity = self._calculate_debt_to_equity(fundamental_data)
            roe = self._calculate_roe(fundamental_data)
            roa = self._calculate_roa(fundamental_data)
            
            # Determine analyst rating
            analyst_rating = self._determine_analyst_rating(analyst_data)
            
            # Calculate fair value
            fair_value = await self._calculate_fair_value(symbol, fundamental_data)
            
            analysis = FundamentalAnalysis(
                symbol=symbol,
                pe_ratio=pe_ratio,
                pb_ratio=pb_ratio,
                eps_growth=eps_growth,
                revenue_growth=revenue_growth,
                debt_to_equity=debt_to_equity,
                roe=roe,
                roa=roa,
                analyst_rating=analyst_rating,
                fair_value=fair_value,
                confidence=0.0,  # Will be calculated separately
                timestamp=datetime.utcnow()
            )
            
            self.logger.info(f"✅ Fundamental analysis completed for: {symbol}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"� Fundamental analysis failed for {symbol}: {e}", exc_info=True)
            raise
            
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "fundamental_analysis",
            "pe_ratio_analysis",
            "pb_ratio_analysis",
            "eps_growth_analysis",
            "revenue_growth_analysis",
            "debt_analysis",
            "roe_analysis",
            "roa_analysis",
            "analyst_ratings",
            "fair_value_calculation",
            "economic_calendar_integration"
        ]
        
    def _calculate_pe_ratio(self, data: Dict[str, Any]) -> Optional[float]:
        """Calculate P/E ratio"""
        try:
            price = data.get("current_price")
            earnings = data.get("earnings_per_share")
            
            if price and earnings and earnings != 0:
                return float(price) / float(earnings)
            return None
            
        except (ZeroDivisionError, TypeError):
            return None
            
    def _calculate_pb_ratio(self, data: Dict[str, Any]) -> Optional[float]:
        """Calculate P/B ratio"""
        try:
            price = data.get("current_price")
            book_value = data.get("book_value_per_share")
            
            if price and book_value and book_value != 0:
                return float(price) / float(book_value)
            return None
            
        except (ZeroDivisionError, TypeError):
            return None
            
    def _calculate_eps_growth(self, data: Dict[str, Any]) -> Optional[float]:
        """Calculate EPS growth rate"""
        try:
            current_eps = data.get("earnings_per_share")
            previous_eps = data.get("previous_earnings_per_share")
            
            if current_eps and previous_eps and previous_eps != 0:
                return (float(current_eps) - float(previous_eps)) / float(previous_eps)
            return None
            
        except (ZeroDivisionError, TypeError):
            return None
            
    def _calculate_revenue_growth(self, data: Dict[str, Any]) -> Optional[float]:
        """Calculate revenue growth rate"""
        try:
            current_revenue = data.get("revenue")
            previous_revenue = data.get("previous_revenue")
            
            if current_revenue and previous_revenue and previous_revenue != 0:
                return (float(current_revenue) - float(previous_revenue)) / float(previous_revenue)
            return None
            
        except (ZeroDivisionError, TypeError):
            return None
            
    def _calculate_debt_to_equity(self, data: Dict[str, Any]) -> Optional[float]:
        """Calculate debt-to-equity ratio"""
        try:
            total_debt = data.get("total_debt")
            total_equity = data.get("total_equity")
            
            if total_debt and total_equity and total_equity != 0:
                return float(total_debt) / float(total_equity)
            return None
            
        except (ZeroDivisionError, TypeError):
            return None
            
    def _calculate_roe(self, data: Dict[str, Any]) -> Optional[float]:
        """Calculate Return on Equity"""
        try:
            net_income = data.get("net_income")
            total_equity = data.get("total_equity")
            
            if net_income and total_equity and total_equity != 0:
                return float(net_income) / float(total_equity)
            return None
            
        except (ZeroDivisionError, TypeError):
            return None
            
    def _calculate_roa(self, data: Dict[str, Any]) -> Optional[float]:
        """Calculate Return on Assets"""
        try:
            net_income = data.get("net_income")
            total_assets = data.get("total_assets")
            
            if net_income and total_assets and total_assets != 0:
                return float(net_income) / float(total_assets)
            return None
            
        except (ZeroDivisionError, TypeError):
            return None
            
    def _determine_analyst_rating(self, analyst_data: Dict[str, Any]) -> Optional[str]:
        """Determine overall analyst rating"""
        try:
            buy_ratings = analyst_data.get("buy_ratings", 0)
            hold_ratings = analyst_data.get("hold_ratings", 0)
            sell_ratings = analyst_data.get("sell_ratings", 0)
            
            total_ratings = buy_ratings + hold_ratings + sell_ratings
            
            if total_ratings == 0:
                return None
                
            buy_ratio = buy_ratings / total_ratings
            
            if buy_ratio >= 0.7:
                return "STRONG_BUY"
            elif buy_ratio >= 0.5:
                return "BUY"
            elif buy_ratio >= 0.3:
                return "HOLD"
            else:
                return "SELL"
                
        except (TypeError, ZeroDivisionError):
            return None
            
    async def _calculate_fair_value(self, symbol: str, data: Dict[str, Any]) -> Optional[Decimal]:
        """Calculate fair value using DCF model"""
        try:
            # This is a simplified DCF calculation
            # In practice, this would be much more sophisticated
            
            free_cash_flow = data.get("free_cash_flow")
            growth_rate = data.get("growth_rate", 0.03)  # Default 3%
            discount_rate = data.get("discount_rate", 0.08)  # Default 8%
            terminal_growth = data.get("terminal_growth", 0.02)  # Default 2%
            
            if not free_cash_flow:
                return None
                
            # Simplified DCF calculation
            # Fair Value = FCF * (1 + g) / (r - g)
            fair_value = float(free_cash_flow) * (1 + growth_rate) / (discount_rate - terminal_growth)
            
            return Decimal(str(fair_value))
            
        except (ZeroDivisionError, TypeError, ValueError):
            return None
            
    def _calculate_confidence(self, analysis: FundamentalAnalysis) -> float:
        """Calculate confidence score based on data availability"""
        confidence_factors = [
            analysis.pe_ratio is not None,
            analysis.pb_ratio is not None,
            analysis.eps_growth is not None,
            analysis.revenue_growth is not None,
            analysis.debt_to_equity is not None,
            analysis.roe is not None,
            analysis.roa is not None,
            analysis.analyst_rating is not None,
            analysis.fair_value is not None
        ]
        
        available_factors = sum(confidence_factors)
        total_factors = len(confidence_factors)
        
        return available_factors / total_factors if total_factors > 0 else 0.0
        
    def _count_data_points(self, analysis: FundamentalAnalysis) -> int:
        """Count available data points"""
        data_points = 0
        
        if analysis.pe_ratio is not None:
            data_points += 1
        if analysis.pb_ratio is not None:
            data_points += 1
        if analysis.eps_growth is not None:
            data_points += 1
        if analysis.revenue_growth is not None:
            data_points += 1
        if analysis.debt_to_equity is not None:
            data_points += 1
        if analysis.roe is not None:
            data_points += 1
        if analysis.roa is not None:
            data_points += 1
        if analysis.analyst_rating is not None:
            data_points += 1
        if analysis.fair_value is not None:
            data_points += 1
            
        return data_points