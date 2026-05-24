"""
Agent Registry and Orchestration System
Central coordination point for all PRIV agents using Pub/Sub
"""

import logging
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from backend.communication.agent_base import Agent
from backend.communication.pubsub_broker import get_broker, publish_to_topic

logger = logging.getLogger(__name__)


@dataclass
class AgentRegistration:
    """Information about a registered agent"""
    agent_id: str
    agent_type: str
    status: str = "registered"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    topics: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    """
    Registry for all PRIV agents
    Manages agent lifecycle, discovery, and coordination
    """
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._registrations: Dict[str, AgentRegistration] = {}
        self._agent_types: Dict[str, List[str]] = {}  # type -> [agent_ids]
        self.broker = get_broker()
        logger.info("AgentRegistry initialized")
    
    def register_agent(self, agent: Agent, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register an agent with the registry"""
        if agent.agent_id in self._agents:
            logger.warning(f"Agent {agent.agent_id} already registered")
            return
        
        self._agents[agent.agent_id] = agent
        self._registrations[agent.agent_id] = AgentRegistration(
            agent_id=agent.agent_id,
            agent_type=agent.agent_type,
            topics=agent.subscribe_topics,
            metadata=metadata or {}
        )
        
        # Index by type
        if agent.agent_type not in self._agent_types:
            self._agent_types[agent.agent_type] = []
        self._agent_types[agent.agent_type].append(agent.agent_id)
        
        logger.info(f"Registered agent {agent.agent_id} ({agent.agent_type})")
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID"""
        return self._agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: str) -> List[Agent]:
        """Get all agents of a specific type"""
        agent_ids = self._agent_types.get(agent_type, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def list_agents(self) -> List[AgentRegistration]:
        """List all registered agents"""
        return list(self._registrations.values())
    
    def get_agent_count(self) -> int:
        """Get total number of registered agents"""
        return len(self._agents)
    
    def get_agent_count_by_type(self, agent_type: str) -> int:
        """Get number of agents of a specific type"""
        return len(self._agent_types.get(agent_type, []))
    
    async def start_all_agents(self) -> None:
        """Start all registered agents"""
        logger.info(f"Starting {len(self._agents)} agents...")
        tasks = [agent.start() for agent in self._agents.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        failed = sum(1 for r in results if isinstance(r, Exception))
        logger.info(f"Started agents: {len(self._agents) - failed} successful, {failed} failed")
    
    async def stop_all_agents(self) -> None:
        """Stop all registered agents"""
        logger.info(f"Stopping {len(self._agents)} agents...")
        tasks = [agent.stop() for agent in self._agents.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All agents stopped")
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report for all agents"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_agents": len(self._agents),
            "agents_by_type": {
                atype: len(agents) 
                for atype, agents in self._agent_types.items()
            },
            "agents": [agent.get_status() for agent in self._agents.values()],
            "broker_connected": self.broker.is_connected,
            "broker_topics": len(self.broker.get_topics())
        }


class AgentOrchestrator:
    """
    Coordinates communication between agents via Pub/Sub
    Handles complex workflows and inter-agent coordination
    """
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.broker = get_broker()
        self._workflows: Dict[str, Any] = {}
        logger.info("AgentOrchestrator initialized")
    
    async def start_trading_workflow(
        self,
        symbols: List[str],
        strategy: str = "default"
    ) -> str:
        """
        Start a trading workflow
        Coordinates strategist, risk, execution, and other agents
        """
        workflow_id = f"trade-{datetime.utcnow().isoformat()}"
        logger.info(f"Starting trading workflow {workflow_id} for symbols {symbols}")
        
        # Publish to strategist agent(s)
        strategists = self.registry.get_agents_by_type("strategist")
        for strategist in strategists:
            await strategist.publish_message(
                f"workflow.{workflow_id}",
                {
                    "workflow_id": workflow_id,
                    "symbols": symbols,
                    "strategy": strategy,
                    "action": "generate_proposals"
                }
            )
        
        self._workflows[workflow_id] = {
            "status": "running",
            "created_at": datetime.utcnow().isoformat(),
            "symbols": symbols,
            "strategy": strategy
        }
        
        return workflow_id
    
    async def start_risk_analysis_workflow(
        self,
        symbols: List[str],
        portfolio_id: Optional[str] = None
    ) -> str:
        """Start a risk analysis workflow"""
        workflow_id = f"risk-{datetime.utcnow().isoformat()}"
        logger.info(f"Starting risk analysis workflow {workflow_id}")
        
        # Publish to risk agent(s)
        risk_agents = self.registry.get_agents_by_type("risk")
        for risk_agent in risk_agents:
            await risk_agent.publish_message(
                f"workflow.{workflow_id}",
                {
                    "workflow_id": workflow_id,
                    "symbols": symbols,
                    "portfolio_id": portfolio_id,
                    "action": "analyze_risk"
                }
            )
        
        self._workflows[workflow_id] = {
            "status": "running",
            "created_at": datetime.utcnow().isoformat(),
            "symbols": symbols,
            "portfolio_id": portfolio_id
        }
        
        return workflow_id
    
    async def start_news_analysis_workflow(self) -> str:
        """Start a news analysis workflow"""
        workflow_id = f"news-{datetime.utcnow().isoformat()}"
        logger.info(f"Starting news analysis workflow {workflow_id}")
        
        # Publish to news analysis agent(s)
        news_agents = self.registry.get_agents_by_type("news_analysis")
        for news_agent in news_agents:
            await news_agent.publish_message(
                f"workflow.{workflow_id}",
                {
                    "workflow_id": workflow_id,
                    "action": "analyze_news"
                }
            )
        
        self._workflows[workflow_id] = {
            "status": "running",
            "created_at": datetime.utcnow().isoformat()
        }
        
        return workflow_id
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow"""
        return self._workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all active workflows"""
        return list(self._workflows.values())


# Global instances
_registry: Optional[AgentRegistry] = None
_orchestrator: Optional[AgentOrchestrator] = None


def get_registry() -> AgentRegistry:
    """Get or create the global agent registry"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def get_orchestrator() -> AgentOrchestrator:
    """Get or create the global agent orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator(get_registry())
    return _orchestrator
