"""
PRIV Core Engine

The central intelligence engine for PRIV system operations.
Coordinates all PRIV components and provides unified system management.

Author: SansMercantile™ AI Development Team
Attribution: MezzofortePrivilege (mezzoforte@sansmercantile.com)
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from ..multi_agent.priv_ai_ops_agent import PrivAIOpsAgent
from ..multi_agent.priv_risk_agent import PrivRiskAgent
from ..multi_agent.priv_strategist_agent import PrivStrategistAgent as PRIVStrategyAgent
from ..multi_agent.priv_notification_agent import PRIVNotificationAgent
from ..trading_engine.priv_trading_engine import PRIVTradingEngine
from ..data_sourcing.fundamental_data_ingestor import FundamentalDataIngestor
from ..risk_analysis.risk_analyzer import RiskAnalyzer
from .personality_integration import get_priv_personality

logger = logging.getLogger(__name__)


class PRIVCoreEngine:
    """
    Central intelligence engine for PRIV system.
    Coordinates all PRIV components and provides unified system management.
    """
    
    def __init__(self):
        self.personality = get_priv_personality()
        self.agents = {}
        self.engines = {}
        self.is_initialized = False
        self.health_status = {}
        
    async def initialize(self) -> bool:
        """
        Initialize the PRIV core engine and all its components.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.personality.log_with_identity("🚀 Initializing PRIV Core Engine")
            
            # Initialize all agents
            self.agents = {
                "ops": PrivAIOpsAgent(),
                "risk": PrivRiskAgent(),
                "strategy": PRIVStrategyAgent(),
                "notification": PRIVNotificationAgent()
            }
            
            # Initialize all engines
            self.engines = {
                "trading": PRIVTradingEngine(),
                "data": FundamentalDataIngestor(),
                "risk": RiskAnalyzer()
            }
            
            # Initialize each component
            for name, agent in self.agents.items():
                await agent.initialize()
                self.health_status[name] = "healthy"
                
            for name, engine in self.engines.items():
                if hasattr(engine, 'initialize'):
                    await engine.initialize()
                self.health_status[name] = "healthy"
                
            self.is_initialized = True
            self.personality.log_with_identity("✅ PRIV Core Engine initialized successfully")
            return True
            
        except Exception as e:
            self.personality.log_with_identity(f"❌ PRIV Core Engine initialization failed: {e}", level="error")
            return False
            
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check on all PRIV components.
        
        Returns:
            Dict containing health status of all components
        """
        try:
            health_report = {
                "system": "PRIV",
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "healthy",
                "components": {},
                "summary": {}
            }
            
            # Check each agent
            for name, agent in self.agents.items():
                try:
                    if hasattr(agent, 'health_check'):
                        health_report["components"][name] = await agent.health_check()
                    else:
                        health_report["components"][name] = {"status": "healthy", "agent": name}
                except Exception as e:
                    health_report["components"][name] = {"status": "unhealthy", "error": str(e)}
                    
            # Check each engine
            for name, engine in self.engines.items():
                try:
                    if hasattr(engine, 'health_check'):
                        health_report["components"][name] = await engine.health_check()
                    else:
                        health_report["components"][name] = {"status": "healthy", "engine": name}
                except Exception as e:
                    health_report["components"][name] = {"status": "unhealthy", "error": str(e)}
                    
            # Calculate summary
            total_components = len(health_report["components"])
            healthy_components = sum(1 for c in health_report["components"].values() if c.get("status") == "healthy")
            
            health_report["summary"] = {
                "total_components": total_components,
                "healthy_components": healthy_components,
                "health_percentage": (healthy_components / total_components) * 100
            }
            
            if healthy_components != total_components:
                health_report["overall_status"] = "degraded"
                
            return health_report
            
        except Exception as e:
            return {
                "system": "PRIV",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
    async def process_financial_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a financial intelligence request through PRIV system.
        
        Args:
            request: Financial request containing ticker, analysis type, etc.
            
        Returns:
            Comprehensive financial analysis response
        """
        if not self.is_initialized:
            return {"error": "PRIV Core Engine not initialized"}
            
        try:
            self.personality.log_with_identity(f"Processing financial request: {request}")
            
            # Extract request parameters
            ticker = request.get("ticker")
            analysis_type = request.get("analysis_type", "comprehensive")
            
            if not ticker:
                return {"error": "Ticker symbol required"}
                
            # Orchestrate multi-agent analysis
            response = {
                "ticker": ticker,
                "analysis_type": analysis_type,
                "timestamp": datetime.utcnow().isoformat(),
                "results": {}
            }
            
            # Get fundamental data
            if "data" in self.engines:
                fundamental_data = await self.engines["data"].fetch_fundamental_data(ticker)
                response["results"]["fundamental_analysis"] = fundamental_data.dict()
                
            # Risk analysis
            if "risk" in self.engines:
                risk_analysis = await self.engines["risk"].analyze_risk(ticker, fundamental_data)
                response["results"]["risk_analysis"] = risk_analysis
                
            # Trading analysis
            if "trading" in self.engines:
                trading_analysis = await self.engines["trading"].analyze_trading_opportunities(ticker)
                response["results"]["trading_analysis"] = trading_analysis
                
            # Multi-agent insights
            if "strategy" in self.agents:
                strategy_insights = await self.agents["strategy"].generate_strategy(ticker, response["results"])
                response["results"]["strategy_insights"] = strategy_insights
                
            # Risk assessment
            if "risk" in self.agents:
                risk_assessment = await self.agents["risk"].assess_portfolio_risk(ticker, response["results"])
                response["results"]["risk_assessment"] = risk_assessment
                
            # Operations recommendations
            if "ops" in self.agents:
                ops_recommendations = await self.agents["ops"].generate_recommendations(response["results"])
                response["results"]["operations_recommendations"] = ops_recommendations
                
            # Notification summary
            if "notification" in self.agents:
                notification = await self.agents["notification"].create_notification(response)
                response["results"]["notification"] = notification
                
            self.personality.log_with_identity(f"✅ Financial request processed successfully for {ticker}")
            return response
            
        except Exception as e:
            self.personality.log_with_identity(f"❌ Error processing financial request: {e}", level="error")
            return {"error": str(e)}
            
    async def run_system_diagnostics(self) -> Dict[str, Any]:
        """
        Run comprehensive system diagnostics.
        
        Returns:
            Diagnostic report with recommendations
        """
        try:
            self.personality.log_with_identity("🧪 Running PRIV system diagnostics")
            
            diagnostics = {
                "system": "PRIV",
                "diagnostics": {
                    "health_check": await self.health_check(),
                    "performance_metrics": {},
                    "recommendations": []
                }
            }
            
            # Performance metrics
            start_time = datetime.utcnow()
            health = await self.health_check()
            end_time = datetime.utcnow()
            
            diagnostics["diagnostics"]["performance_metrics"] = {
                "health_check_duration_ms": (end_time - start_time).total_seconds() * 1000,
                "memory_usage": "healthy",  # Add actual memory monitoring
                "cpu_usage": "healthy",     # Add actual CPU monitoring
                "disk_usage": "healthy"     # Add actual disk monitoring
            }
            
            # Generate recommendations based on health
            for component, status in health.get("components", {}).items():
                if status.get("status") != "healthy":
                    diagnostics["diagnostics"]["recommendations"].append(
                        f"Investigate {component} component health"
                    )
                    
            self.personality.log_with_identity("✅ PRIV system diagnostics completed")
            return diagnostics
            
        except Exception as e:
            self.personality.log_with_identity(f"❌ Error running diagnostics: {e}", level="error")
            return {"error": str(e)}
            
    async def shutdown(self):
        """Gracefully shutdown all PRIV components."""
        try:
            self.personality.log_with_identity("🛑 Shutting down PRIV Core Engine")
            
            # Shutdown agents
            for name, agent in self.agents.items():
                if hasattr(agent, 'shutdown'):
                    await agent.shutdown()
                    
            # Shutdown engines
            for name, engine in self.engines.items():
                if hasattr(engine, 'shutdown'):
                    await engine.shutdown()
                    
            self.is_initialized = False
            self.personality.log_with_identity("✅ PRIV Core Engine shutdown complete")
            
        except Exception as e:
            self.personality.log_with_identity(f"❌ Error during shutdown: {e}", level="error")


# Global instance
_priv_core_engine = None


def get_priv_core_engine() -> PRIVCoreEngine:
    """Get the global PRIV core engine instance."""
    global _priv_core_engine
    if _priv_core_engine is None:
        _priv_core_engine = PRIVCoreEngine()
    return _priv_core_engine


async def initialize_priv_system() -> bool:
    """
    Initialize the complete PRIV system.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    engine = get_priv_core_engine()
    return await engine.initialize()


async def run_priv_diagnostics() -> Dict[str, Any]:
    """Run PRIV system diagnostics."""
    engine = get_priv_core_engine()
    return await engine.run_system_diagnostics()


async def process_priv_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Process a financial request through PRIV."""
    engine = get_priv_core_engine()
    return await engine.process_financial_request(request)