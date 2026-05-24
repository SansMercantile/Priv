"""
Agent Migration Adapter
Allows existing agents to work with the new Pub/Sub system with minimal changes.
This provides backward compatibility while transitioning to the new architecture.
"""

import logging
from typing import Dict, Any, Optional, Callable
import asyncio

from backend.communication.agent_base import Agent
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)


class PrivAgentAdapter(Agent):
    """
    Adapter to wrap old PrivAgent-style agents with the new Agent base class
    Allows existing agents to work without major refactoring
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        old_agent_class,
        message_broker: Optional[MessageBrokerInterface] = None,
        broker: Optional[BrokerInterface] = None,
        persona: Optional[Dict[str, Any]] = None,
        topics: Optional[list] = None
    ):
        """
        Initialize the adapter
        
        Args:
            agent_id: Agent ID
            agent_type: Agent type
            old_agent_class: The old agent class to wrap
            message_broker: Old-style message broker (optional)
            broker: Trading broker interface (optional)
            persona: Agent persona data (optional)
            topics: Topics to subscribe to
        """
        super().__init__(agent_id, agent_type, topics or [f"agent.{agent_type}"])
        
        self.message_broker = message_broker
        self.broker = broker
        self.persona = persona or {}
        
        # Instantiate the old agent class
        self.old_agent = old_agent_class(
            agent_id=agent_id,
            agent_type=agent_type,
            message_broker=message_broker,
            broker=broker,
            persona=persona
        )
        
        # Store old agent methods
        self._old_handlers: Dict[str, Callable] = {}
    
    async def _initialize(self) -> None:
        """Initialize the old agent if it has a start method"""
        try:
            if hasattr(self.old_agent, 'start'):
                await self.old_agent.start()
                logger.info(f"Old agent {self.agent_id} started via adapter")
        except Exception as e:
            logger.error(f"Error initializing old agent {self.agent_id}: {e}")
    
    async def _cleanup(self) -> None:
        """Clean up the old agent if it has a stop method"""
        try:
            if hasattr(self.old_agent, 'stop'):
                await self.old_agent.stop()
                logger.info(f"Old agent {self.agent_id} stopped via adapter")
        except Exception as e:
            logger.error(f"Error cleaning up old agent {self.agent_id}: {e}")
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process messages using the old agent's methods
        Maps Pub/Sub messages to old agent methods
        """
        message_type = message.get("type", message.get("message_type", ""))
        payload = message.get("payload", message)
        
        # Try to find a handler for this message type
        handler_name = f"_handle_{message_type}_message"
        if hasattr(self.old_agent, handler_name):
            try:
                handler = getattr(self.old_agent, handler_name)
                # Call the handler (it might be async or sync)
                if asyncio.iscoroutinefunction(handler):
                    await handler(payload)
                else:
                    handler(payload)
                logger.debug(f"Old agent {self.agent_id} handled {message_type} message")
            except Exception as e:
                logger.error(f"Error in handler {handler_name}: {e}")
        
        # Try generic process method
        if hasattr(self.old_agent, 'process_message'):
            try:
                method = getattr(self.old_agent, 'process_message')
                if asyncio.iscoroutinefunction(method):
                    result = await method(message)
                else:
                    result = method(message)
                
                if result is not None:
                    return result if isinstance(result, dict) else {"status": "processed"}
            except Exception as e:
                logger.error(f"Error in process_message: {e}")
        
        return None
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a custom handler for a message type"""
        self._old_handlers[message_type] = handler


class SimplifiedAgentFactory:
    """
    Factory for creating agents that work with both old and new systems
    Simplifies agent creation and registration
    """
    
    @staticmethod
    def create_strategist_agent(
        agent_id: str = "strategist-001",
        use_adapter: bool = False
    ) -> Agent:
        """Create a strategist agent"""
        if use_adapter:
            from backend.multi_agent.priv_strategist_agent import PrivStrategistAgent
            return PrivAgentAdapter(
                agent_id=agent_id,
                agent_type="strategist",
                old_agent_class=PrivStrategistAgent,
                topics=["agent.strategist", "workflow.trade"]
            )
        else:
            # Return native Agent implementation
            from backend.agents.strategist_agent import StrategistAgent
            return StrategistAgent(agent_id=agent_id)
    
    @staticmethod
    def create_risk_agent(
        agent_id: str = "risk-001",
        use_adapter: bool = False
    ) -> Agent:
        """Create a risk agent"""
        if use_adapter:
            from backend.multi_agent.priv_risk_agent import PrivRiskAgent
            return PrivAgentAdapter(
                agent_id=agent_id,
                agent_type="risk",
                old_agent_class=PrivRiskAgent,
                topics=["agent.risk", "workflow.trade"]
            )
        else:
            from backend.agents.risk_agent import RiskAgent
            return RiskAgent(agent_id=agent_id)
    
    @staticmethod
    def create_execution_agent(
        agent_id: str = "execution-001",
        use_adapter: bool = False
    ) -> Agent:
        """Create an execution agent"""
        if use_adapter:
            from backend.multi_agent.priv_execution_agent import PrivExecutionAgent
            return PrivAgentAdapter(
                agent_id=agent_id,
                agent_type="execution",
                old_agent_class=PrivExecutionAgent,
                topics=["agent.execution", "workflow.trade"]
            )
        else:
            from backend.agents.execution_agent import ExecutionAgent
            return ExecutionAgent(agent_id=agent_id)
    
    @staticmethod
    def create_all_agents(use_adapter: bool = False) -> list:
        """Create all standard agents"""
        agents = []
        
        # Create core agents
        agents.append(SimplifiedAgentFactory.create_strategist_agent(use_adapter=use_adapter))
        agents.append(SimplifiedAgentFactory.create_risk_agent(use_adapter=use_adapter))
        agents.append(SimplifiedAgentFactory.create_execution_agent(use_adapter=use_adapter))
        
        # Create specialized agents
        agent_types = [
            ("sentiment", "sentiment-001"),
            ("news_analysis", "news-001"),
            ("technical", "technical-001"),
            ("quantitative", "quant-001"),
            ("compliance", "compliance-001"),
            ("portfolio_manager", "portfolio-001"),
        ]
        
        for agent_type, agent_id in agent_types:
            agent = Agent(agent_id, agent_type, [f"agent.{agent_type}"])
            agents.append(agent)
        
        return agents


def create_migration_context():
    """
    Create a context for migrating agents
    Returns an object that can help with the migration process
    """
    return {
        "factory": SimplifiedAgentFactory,
        "adapter": PrivAgentAdapter,
        "steps": [
            "1. Create agents using factory or adapter",
            "2. Register agents with registry",
            "3. Start agents",
            "4. Test message passing",
            "5. Update agent implementations to native Agent class",
            "6. Remove adapters once all agents are migrated"
        ]
    }
