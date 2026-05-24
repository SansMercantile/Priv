# priv/backend/multi_agent/departmental_api.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from backend.multi_agent.priv_agent_protocol import AgentType, AgentMessage, AgentState
from backend.multi_agent.departmental_orchestrator import DepartmentalOrchestrator
from backend.multi_agent.corporate_memory_graph import CorporateMemoryGraph

router = APIRouter()

# --- Dependency Functions ---
# These functions get the instances managed by PRIV's Central Orchestrator
def get_priv_departmental_orchestrator() -> DepartmentalOrchestrator:
    """
    Dependency to get the running instance of PRIV's Departmental Orchestrator.
    """
    from backend.main import priv_central_orchestrator_instance  # Deferred import

    if priv_central_orchestrator_instance and priv_central_orchestrator_instance.departmental_orchestrator:
        return priv_central_orchestrator_instance.departmental_orchestrator
    raise HTTPException(status_code=503, detail="PRIV Departmental Orchestrator not initialized or running.")

def get_priv_corporate_memory_graph() -> CorporateMemoryGraph:
    """
    Dependency to get the running instance of PRIV's Corporate Memory Graph.
    This assumes CorporateMemoryGraph is managed as a singleton or accessible via CentralOrchestrator.
    For now, we'll assume it's a singleton in dependencies.py as per your original code.
    """
    from backend.dependencies import get_corporate_memory_graph
    return get_corporate_memory_graph()


# --- Existing and Preserved Endpoints ---

@router.post("/task", status_code=202)
async def route_departmental_task(
    task_data: Dict[str, Any],
    dept_orchestrator: DepartmentalOrchestrator = Depends(get_priv_departmental_orchestrator)
):
    """
    Routes a task to the appropriate departmental agent.
    """
    agent_id = task_data.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="'agent_id' must be specified in task_data.")
    
    agent = dept_orchestrator.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Departmental Agent {agent_id} not found.")
    
    # Construct an AgentMessage for the internal agent communication
    agent_message = AgentMessage(
        sender_id="api_gateway_router",
        sender_type=AgentType.EXTERNAL_API,
        recipient_id=agent_id,
        message_type=task_data.get("type", "generic_task"),
        content=task_data.get("content", task_data) # Pass full task_data as content
    )
    await agent.task_queue.put(agent_message) # Put task into agent's queue
    
    return {"message": f"Task routed successfully to agent {agent_id}."}

@router.post("/memory", status_code=201)
async def add_to_corporate_memory(
    memory_data: Dict[str, Any],
    memory_graph: CorporateMemoryGraph = Depends(get_priv_corporate_memory_graph)
):
    """
    Adds a new node or edge to the corporate memory graph.
    """
    node_id = memory_data.get("node_id")
    node_type = memory_data.get("node_type")
    attributes = memory_data.get("attributes", {})
    
    if node_id and node_type:
        memory_graph.add_node(node_id, node_type, attributes)
        return {"message": f"Node {node_id} added to corporate memory."}
    else:
        raise HTTPException(status_code=400, detail="Missing node_id or node_type.")

# --- New Endpoints (as discussed previously) ---

@router.get("/departmental-agents", response_model=List[Dict[str, Any]])
async def get_departmental_agents(
    dept_orchestrator: DepartmentalOrchestrator = Depends(get_priv_departmental_orchestrator)
):
    """
    Retrieves a list of all managed departmental agents.
    """
    return [
        {"agent_id": agent.agent_id, "agent_type": agent.agent_type.value, "status": agent.state.value}
        for agent in dept_orchestrator.agents.values()
    ]

@router.post("/departmental-agents/{agent_id}/send-message")
async def send_message_to_departmental_agent(
    agent_id: str, 
    message: Dict[str, Any],
    dept_orchestrator: DepartmentalOrchestrator = Depends(get_priv_departmental_orchestrator)
):
    """
    Sends a message to a specific departmental agent.
    """
    agent = dept_orchestrator.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Departmental Agent {agent_id} not found.")
    
    agent_message = AgentMessage(
        sender_id="api_gateway",
        sender_type=AgentType.EXTERNAL_API,
        recipient_id=agent_id,
        message_type=message.get("type", "generic_command"),
        content=message.get("content", {})
    )
    
    await agent.task_queue.put(agent_message)
    
    return {"status": "message sent", "agent_id": agent_id, "message_type": message.get("type")}

