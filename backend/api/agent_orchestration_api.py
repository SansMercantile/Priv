"""
Unified Agent Orchestration API
Integrates Pub/Sub-based agent communication with REST endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging


from backend.communication.agent_registry import get_registry, get_orchestrator
from backend.communication.pubsub_broker import get_broker, send_request

logger = logging.getLogger(__name__)

router = APIRouter()


class TradeWorkflowRequest(BaseModel):
    symbols: List[str] = Field(default_factory=list)
    strategy: str = "default"


class RiskWorkflowRequest(BaseModel):
    symbols: List[str] = Field(default_factory=list)
    portfolio_id: Optional[str] = None


class PublishMessageRequest(BaseModel):
    topic: str
    message: Dict[str, Any]


@router.get("/registry/agents")

async def list_all_agents() -> Dict[str, Any]:
    """List all registered agents"""
    try:
        registry = get_registry()
        agents = registry.list_agents()
        return {
            "success": True,
            "data": {
                "total_agents": len(agents),
                "agents": [
                    {
                        "agent_id": a.agent_id,
                        "agent_type": a.agent_type,
                        "status": a.status,
                        "created_at": a.created_at,
                        "topics": a.topics,
                        "metadata": a.metadata
                    }
                    for a in agents
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/agents/{agent_type}")
async def list_agents_by_type(agent_type: str) -> Dict[str, Any]:
    """List agents of a specific type"""
    try:
        registry = get_registry()
        agents = registry.get_agents_by_type(agent_type)
        return {
            "success": True,
            "data": {
                "agent_type": agent_type,
                "count": len(agents),
                "agents": [a.get_status() for a in agents]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing agents of type {agent_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/agents/{agent_id}/status")
async def get_agent_status(agent_id: str) -> Dict[str, Any]:
    """Get status of a specific agent"""
    try:
        registry = get_registry()
        agent = registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return {
            "success": True,
            "data": agent.get_status(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/status")
async def get_registry_status() -> Dict[str, Any]:
    """Get overall registry status"""
    try:
        registry = get_registry()
        return {
            "success": True,
            "data": {
                "total_agents": registry.get_agent_count(),
                "agents_by_type": {
                    atype: registry.get_agent_count_by_type(atype)
                    for atype in ["strategist", "risk", "execution", "sentiment", "portfolio_manager",
                                 "technical", "quantitative", "news_analysis", "compliance", "tax",
                                 "legal", "research", "arbitrage", "commodity", "economic", "forex",
                                 "futures", "options", "political", "yield_optimizer"]
                },
                "broker_status": {
                    "connected": registry.broker.is_connected,
                    "active_topics": len(registry.broker.get_topics())
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting registry status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestration/trade-workflow")
async def start_trade_workflow(request: TradeWorkflowRequest) -> Dict[str, Any]:

    """
    Start a trading workflow
    Coordinates strategist, risk, execution agents
    """
    try:
        orchestrator = get_orchestrator()
        workflow_id = await orchestrator.start_trading_workflow(request.symbols, request.strategy)
        return {
            "success": True,
            "data": {
                "workflow_id": workflow_id,
                "status": "started",
                "symbols": request.symbols,
                "strategy": request.strategy
            },

            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting trade workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestration/risk-workflow")
async def start_risk_workflow(request: RiskWorkflowRequest) -> Dict[str, Any]:

    """
    Start a risk analysis workflow
    Coordinates risk agents
    """
    try:
        orchestrator = get_orchestrator()
        workflow_id = await orchestrator.start_risk_analysis_workflow(request.symbols, request.portfolio_id)
        return {
            "success": True,
            "data": {
                "workflow_id": workflow_id,
                "status": "started",
                "symbols": request.symbols,
                "portfolio_id": request.portfolio_id
            },

            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting risk workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestration/news-workflow")
async def start_news_workflow() -> Dict[str, Any]:
    """
    Start a news analysis workflow
    Coordinates news analysis agents
    """
    try:
        orchestrator = get_orchestrator()
        workflow_id = await orchestrator.start_news_analysis_workflow()
        return {
            "success": True,
            "data": {
                "workflow_id": workflow_id,
                "status": "started"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting news workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orchestration/workflows")
async def list_workflows() -> Dict[str, Any]:
    """List all active workflows"""
    try:
        orchestrator = get_orchestrator()
        workflows = orchestrator.list_workflows()
        return {
            "success": True,
            "data": {
                "count": len(workflows),
                "workflows": workflows
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orchestration/workflows/{workflow_id}")
async def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """Get status of a specific workflow"""
    try:
        orchestrator = get_orchestrator()
        workflow = orchestrator.get_workflow_status(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        
        return {
            "success": True,
            "data": workflow,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broker/publish")
async def publish_message(request: PublishMessageRequest) -> Dict[str, Any]:

    """
    Publish a message to a topic (for testing)
    """
    try:
        broker = get_broker()
        await broker.publish_message(request.topic, request.message, sender_id="api-client")
        return {
            "success": True,
            "data": {
                "topic": request.topic,
                "message_id": request.message.get("id", "unknown"),
                "status": "published"
            },

            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error publishing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/broker/topics")
async def list_topics() -> Dict[str, Any]:
    """List all active Pub/Sub topics"""
    try:
        broker = get_broker()
        topics = broker.get_topics()
        return {
            "success": True,
            "data": {
                "count": len(topics),
                "topics": topics
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
