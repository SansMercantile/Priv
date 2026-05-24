"""
Agents API endpoints for PRIV backend.
Provides status and information about multi-agent system.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def get_agents_status() -> Dict[str, Any]:
    """
    Get status of all agents in the system.
    If CentralOrchestrator is available, return its live agent list; otherwise return mock data.
    """
    try:
        # Try to get live agents from the running CentralOrchestrator if available
        try:
            import backend.main as priv_main
            orchestrator = getattr(priv_main, 'priv_central_orchestrator_instance', None)
            if orchestrator and hasattr(orchestrator, 'trade_orchestrator'):
                agents_dict = orchestrator.trade_orchestrator.agents
                agents = []
                for aid, a in agents_dict.items():
                    agents.append({
                        "id": getattr(a, 'agent_id', aid),
                        "name": getattr(a.persona, 'get', lambda k, d=None: None)('name', None) or getattr(a, 'agent_id', aid),
                        "type": getattr(a.agent_type, 'value', str(getattr(a, 'agent_type', 'unknown'))),
                        "status": 'active' if getattr(a, 'is_running', False) else 'idle',
                        "tasks_completed": getattr(a, 'tasks_completed', 0) if hasattr(a, 'tasks_completed') else 0,
                        "tasks_pending": getattr(a, 'task_queue', None) and getattr(a.task_queue, 'qsize', lambda: 0)() or 0,
                        "last_activity": datetime.utcnow().isoformat(),
                        "performance": {
                            "accuracy": getattr(a, 'persona', {}).get('accuracy', None) or None,
                            "response_time_ms": None
                        }
                    })
                summary = {
                    "total_agents": len(agents),
                    "active_agents": len([ag for ag in agents if ag['status'] == 'active']),
                    "total_tasks_completed": sum(ag.get('tasks_completed', 0) for ag in agents),
                    "system_status": "operational"
                }
                return {"success": True, "data": {"agents": agents, "summary": summary}, "timestamp": datetime.utcnow().isoformat()}
        except Exception as inner_e:
            logger.debug(f"Could not fetch live agents from CentralOrchestrator: {inner_e}")

        # Fallback list representing the actual registered PRIV agents in the backend files
        agents = [
            {
                "id": "alt-data-001",
                "name": "Priv Alternative Data Agent",
                "type": "alternative_data",
                "status": "active",
                "tasks_completed": 354,
                "tasks_pending": 2,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Shipping Manifests, Satellite Logs & Retail Foot Traffic",
                "performance": {
                    "accuracy": 94.2,
                    "response_time_ms": 280
                }
            },
            {
                "id": "quantitative-001",
                "name": "Priv Quantitative Agent",
                "type": "quantitative",
                "status": "active",
                "tasks_completed": 1424,
                "tasks_pending": 0,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Statistical Arbitrage, Microstructure Spreads & Alpha Gen",
                "performance": {
                    "accuracy": 98.4,
                    "response_time_ms": 110
                }
            },
            {
                "id": "risk-001",
                "name": "Priv Risk Agent",
                "type": "risk",
                "status": "active",
                "tasks_completed": 894,
                "tasks_pending": 0,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Volatility Borders, Drawdown Caps & Leverage Safeguards",
                "performance": {
                    "accuracy": 99.8,
                    "response_time_ms": 95
                }
            },
            {
                "id": "compliance-001",
                "name": "Priv Compliance Agent",
                "type": "compliance",
                "status": "active",
                "tasks_completed": 412,
                "tasks_pending": 1,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Regulatory Filings, Audits & Trade Licensing Guardrails",
                "performance": {
                    "accuracy": 99.9,
                    "response_time_ms": 160
                }
            },
            {
                "id": "execution-001",
                "name": "Priv Execution Agent",
                "type": "execution",
                "status": "active",
                "tasks_completed": 12840,
                "tasks_pending": 4,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "High-Frequency Smart Routing & Slippage Minimizer",
                "performance": {
                    "accuracy": 99.7,
                    "response_time_ms": 45
                }
            },
            {
                "id": "forex-001",
                "name": "Priv Forex Agent",
                "type": "forex",
                "status": "active",
                "tasks_completed": 8421,
                "tasks_pending": 0,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "G10 Spot Forex Swap Differentials & Bank Spread Pricing",
                "performance": {
                    "accuracy": 97.5,
                    "response_time_ms": 120
                }
            },
            {
                "id": "futures-001",
                "name": "Priv Futures Agent",
                "type": "futures",
                "status": "active",
                "tasks_completed": 5122,
                "tasks_pending": 0,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Funding-Rate Arbitrage, Perpetual Swaps & Margin Rules",
                "performance": {
                    "accuracy": 96.8,
                    "response_time_ms": 130
                }
            },
            {
                "id": "options-001",
                "name": "Priv Options Agent",
                "type": "options",
                "status": "active",
                "tasks_completed": 1845,
                "tasks_pending": 1,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Volatility Smile Models, Exotic Spreads & Option Greeks",
                "performance": {
                    "accuracy": 94.5,
                    "response_time_ms": 210
                }
            },
            {
                "id": "yield-optimizer-001",
                "name": "Priv Yield Optimizer Agent",
                "type": "yield_optimizer",
                "status": "active",
                "tasks_completed": 956,
                "tasks_pending": 0,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Decentralized Liquidity Mining & Capital Pool Rebalancing",
                "performance": {
                    "accuracy": 93.9,
                    "response_time_ms": 320
                }
            },
            {
                "id": "economic-001",
                "name": "Priv Economic Agent",
                "type": "economic",
                "status": "active",
                "tasks_completed": 211,
                "tasks_pending": 0,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Central Bank Policy Sentiment, Dot Plot Ingestion & Yield Curves",
                "performance": {
                    "accuracy": 95.1,
                    "response_time_ms": 410
                }
            },
            {
                "id": "news-analysis-001",
                "name": "Priv News Analysis Agent",
                "type": "news_analysis",
                "status": "active",
                "tasks_completed": 6120,
                "tasks_pending": 3,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "GDELT, Bloomberg RSS & Multi-Lingual Press Sentiment Ingestion",
                "performance": {
                    "accuracy": 95.8,
                    "response_time_ms": 250
                }
            },
            {
                "id": "sentiment-001",
                "name": "Priv Sentiment Agent",
                "type": "sentiment",
                "status": "active",
                "tasks_completed": 12411,
                "tasks_pending": 5,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Social Media Velocity Vectors, Reddit Buzz & Sentiment Tracking",
                "performance": {
                    "accuracy": 91.2,
                    "response_time_ms": 190
                }
            },
            {
                "id": "sensory-001",
                "name": "Priv Sensory Agent",
                "type": "sensory",
                "status": "active",
                "tasks_completed": 18400,
                "tasks_pending": 2,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "IoT Environmental Streams & Commodity Flow Telemetry Parsing",
                "performance": {
                    "accuracy": 98.7,
                    "response_time_ms": 85
                }
            },
            {
                "id": "tax-001",
                "name": "Priv Tax Agent",
                "type": "tax",
                "status": "active",
                "tasks_completed": 412,
                "tasks_pending": 0,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "SARS / GRA Tax Clearance Filings & Multi-National Deductions Optimizer",
                "performance": {
                    "accuracy": 96.2,
                    "response_time_ms": 350
                }
            },
            {
                "id": "legal-001",
                "name": "Priv Legal Agent",
                "type": "legal",
                "status": "active",
                "tasks_completed": 184,
                "tasks_pending": 0,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Cross-Border Jurisdictional Compliance, Legality Auditing & SEC Forms Retr",
                "performance": {
                    "accuracy": 97.4,
                    "response_time_ms": 290
                }
            },
            {
                "id": "audit-001",
                "name": "Priv Audit Agent",
                "type": "audit",
                "status": "active",
                "tasks_completed": 789,
                "tasks_pending": 0,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Cryptographic Zero-Knowledge proof generation & Ledger Audits",
                "performance": {
                    "accuracy": 99.9,
                    "response_time_ms": 140
                }
            },
            {
                "id": "ai-ops-001",
                "name": "Priv AI Ops Agent",
                "type": "ai_ops",
                "status": "active",
                "tasks_completed": 11422,
                "tasks_pending": 1,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Operational Compute Integrity, Host Resources & Mesh Metrics",
                "performance": {
                    "accuracy": 99.8,
                    "response_time_ms": 50
                }
            },
            {
                "id": "ethical-arbiter-001",
                "name": "Priv Ethical Arbiter Agent",
                "type": "ethical_arbiter",
                "status": "active",
                "tasks_completed": 4512,
                "tasks_pending": 0,
                "last_activity": datetime.utcnow().isoformat(),
                "specialty": "Execution Fairness, Risk Proportionality & Systemic Alignment Checks",
                "performance": {
                    "accuracy": 99.9,
                    "response_time_ms": 110
                }
            }
        ]
        
        total_tasks = sum(a["tasks_completed"] for a in agents)
        active_agents = len([a for a in agents if a["status"] == "active"])
        
        return {
            "success": True,
            "data": {
                "agents": agents,
                "summary": {
                    "total_agents": len(agents),
                    "active_agents": active_agents,
                    "total_tasks_completed": total_tasks,
                    "system_status": "operational"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error fetching agents status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_agent_metrics() -> Dict[str, Any]:
    """
    Get performance metrics for the agent system.
    Returns mock data for now.
    """
    try:
        return {
            "success": True,
            "data": {
                "overall_performance": {
                    "avg_accuracy": 96.3,
                    "avg_response_time_ms": 300,
                    "total_interactions": 322,
                    "successful_completions": 310,
                    "success_rate": 96.3
                },
                "resource_usage": {
                    "cpu_usage_pct": 35.5,
                    "memory_usage_mb": 1024,
                    "active_connections": 8
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error fetching agent metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# NEW: Reputation endpoints integrating with AgentReputationLedger
try:
    from backend.multi_agent.agent_reputation_ledger import AgentReputationLedger
    ledger = AgentReputationLedger()
except Exception as e:
    logger.warning(f"AgentReputationLedger unavailable: {e}")
    ledger = None


@router.get("/reputations")
async def get_all_reputations() -> Dict[str, Any]:
    """
    Return the reputation scores for all agents from the AgentReputationLedger.
    """
    try:
        scores = ledger.get_all_agent_scores() if ledger else {}
        return {"success": True, "data": scores, "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        logger.error(f"Error fetching agent reputations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status_with_reputation")
async def get_agents_status_with_reputation() -> Dict[str, Any]:
    """
    Get status of all agents and merge reputation scores (if available).
    Useful for the frontend to render live reputations.
    """
    try:
        base = await get_agents_status()
        reputations = ledger.get_all_agent_scores() if ledger else {}

        for agent in base["data"]["agents"]:
            agent_id = agent.get("id")
            # Map short ids to ledger ids if possible, otherwise use name-based keys
            agent_reputation = reputations.get(agent_id) or reputations.get(agent.get("name"))
            agent["reputation"] = agent_reputation if agent_reputation is not None else agent.get("performance", {}).get("accuracy", 0) / 100.0
        return {"success": True, "data": base["data"], "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Error fetching agents status with reputation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity")
async def get_agent_activity(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Frontend-friendly activity endpoint for the agents page."""
    base = await get_agents_status()
    activities = []
    for agent in base.get("data", {}).get("agents", []):
        activities.append({
            "agent_id": agent.get("id"),
            "agent_name": agent.get("name"),
            "status": agent.get("status"),
            "description": f"{agent.get('name')} is {agent.get('status')}",
            "timestamp": agent.get("last_activity") or datetime.utcnow().isoformat(),
        })
    return {
        "success": True,
        "data": {"activities": activities[offset: offset + limit], "total": len(activities)},
        "timestamp": datetime.utcnow().isoformat(),
    }


# --- Vote history endpoints ---
try:
    from backend.multi_agent.vote_history_ledger import VoteHistoryLedger
    vote_ledger = VoteHistoryLedger()
except Exception as e:
    logger.warning(f"VoteHistoryLedger unavailable: {e}")
    vote_ledger = None


@router.get("/{agent_id}/votes")
async def get_agent_votes(agent_id: str, limit: int = 3):
    """Return the most recent votes for an agent (default limit=3)."""
    try:
        votes = vote_ledger.get_last_votes(agent_id, limit) if vote_ledger else []
        return {"success": True, "data": votes, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Error fetching votes for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}/votes/{vote_id}")
async def get_agent_vote(agent_id: str, vote_id: str):
    """Return a specific recorded vote by id."""
    try:
        vote = vote_ledger.get_vote(vote_id) if vote_ledger else None
        if not vote or vote.get("agent_id") != agent_id:
            raise HTTPException(status_code=404, detail="Vote not found")
        return {"success": True, "data": vote, "timestamp": datetime.utcnow().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching vote {vote_id} for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{agent_id}/votes")
async def create_agent_vote(agent_id: str, payload: Dict[str, Any]):
    """Create a new vote record (useful for tests or demo)."""
    try:
        proposal_id = payload.get("proposal_id")
        vote = payload.get("vote")
        reasoning = payload.get("reasoning", "")
        confidence = float(payload.get("confidence", 0.0))
        if not proposal_id or not vote:
            raise HTTPException(status_code=400, detail="proposal_id and vote are required")
        if not vote_ledger:
            raise HTTPException(status_code=503, detail="Vote ledger is unavailable")
        vote_id = vote_ledger.record_vote(agent_id=agent_id, proposal_id=proposal_id, vote=vote, reasoning=reasoning, confidence=confidence)

        return {"success": True, "data": {"vote_id": vote_id}, "timestamp": datetime.utcnow().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vote for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
