# priv/backend/mpeti_orchestrator.py

import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Google Cloud Imports
try:
    from google.cloud import pubsub_v1
    from google.cloud import firestore
    GCP_AVAILABLE = True
except ImportError:
    pubsub_v1 = None
    firestore = None
    GCP_AVAILABLE = False
    logger.warning("Google Cloud SDK not available. Using local fallback.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
# IMPORTANT: GCP_PROJECT_ID should be set as an environment variable in your deployment.
# For local development, you might use python-dotenv to load it from a .env file.
GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id") 
DISTRIBUTED_TASKS_TOPIC_ID: str = "mpeti-distributed-tasks"
TASK_COLLECTION_NAME: str = "mpeti_distributed_tasks" # Firestore collection

# --- Pub/Sub & Firestore Clients ---
# These clients automatically pick up credentials from the environment
# (e.g., service account key JSON path, or Workload Identity in GKE/Cloud Run).
publisher = pubsub_v1.PublisherClient()
db = firestore.Client(project=GCP_PROJECT_ID)

class MpetiOrchestrator:
    """
    Manages sophisticated task distribution and coordination for multiple,
    independent MPETI agents running in a StatefulSet.
    """
    def __init__(self):
        logger.info("MpetiOrchestrator: Initializing.")
        self.is_running = False
        self.task_monitor_interval_seconds = 30 # How often to check for stale tasks
        self.stale_task_timeout_minutes = 10 # How long before a task is considered stale

    async def start(self):
        """Starts the orchestrator's main loop and background monitoring tasks."""
        if self.is_running:
            logger.info("MpetiOrchestrator is already running.")
            return
        self.is_running = True
        logger.info("MpetiOrchestrator: Starting main loop and task monitoring.")
        
        # Ensure Pub/Sub topic exists
        await self._ensure_pubsub_topic()

        # Start background task to monitor distributed tasks in Firestore
        asyncio.create_task(self._monitor_distributed_tasks())
        logger.info("MpetiOrchestrator: Task monitoring started.")

    async def stop(self):
        """Stops the orchestrator."""
        self.is_running = False
        logger.info("MpetiOrchestrator: Shutting down.")
        # No explicit shutdown for Pub/Sub/Firestore clients needed here,
        # as they manage their own connections.

    async def _ensure_pubsub_topic(self):
        """Ensures the distributed tasks Pub/Sub topic exists."""
        topic_path = publisher.topic_path(GCP_PROJECT_ID, DISTRIBUTED_TASKS_TOPIC_ID)
        try:
            publisher.get_topic(request={"topic": topic_path})
            logger.info(f"Pub/Sub topic '{DISTRIBUTED_TASKS_TOPIC_ID}' already exists.")
        except Exception as e:
            if "NotFound" in str(e):
                publisher.create_topic(request={"name": topic_path})
                logger.info(f"Created Pub/Sub topic: {topic_path}")
            else:
                logger.error(f"Error checking/creating Pub/Sub topic: {e}", exc_info=True)
                raise

    async def create_and_distribute_task(self, task_type: str, description: str, details: Dict[str, Any]) -> str:
        """
        Creates a new distributed task, stores its state in Firestore, and publishes
        it to the Pub/Sub topic for consumption by MPETI agents.

        Args:
            task_type (str): The type of task (e.g., "code_review", "deploy_staging").
            description (str): A brief description of the task.
            details (Dict[str, Any]): Additional task-specific details.

        Returns:
            str: The ID of the created task.
        """
        task_id = f"dist_task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
        
        task_data = {
            "id": task_id,
            "type": task_type,
            "description": description,
            "details": details,
            "status": "pending", # Initial status
            "assigned_to": None,
            "created_at": firestore.SERVER_TIMESTAMP, # Use server timestamp for consistency
            "last_updated_at": firestore.SERVER_TIMESTAMP,
            "retries": 0,
            "orchestrator_notes": []
        }

        # 1. Store task in Firestore
        try:
            await db.collection(TASK_COLLECTION_NAME).document(task_id).set(task_data)
            logger.info(f"Orchestrator: Created Firestore document for task '{task_id}'.")
        except Exception as e:
            logger.error(f"Orchestrator: Failed to create Firestore document for task '{task_id}': {e}", exc_info=True)
            raise

        # 2. Publish task to Pub/Sub
        try:
            message_data = json.dumps(task_data).encode("utf-8")
            topic_path = publisher.topic_path(GCP_PROJECT_ID, DISTRIBUTED_TASKS_TOPIC_ID)
            future = publisher.publish(topic_path, message_data, task_id=task_id)
            # Await the publish operation to ensure it's sent
            message_id = await asyncio.to_thread(future.result) # Use to_thread for blocking call
            logger.info(f"Orchestrator: Published task '{task_id}' to Pub/Sub with message ID: {message_id}")
        except Exception as e:
            logger.error(f"Orchestrator: Failed to publish task '{task_id}' to Pub/Sub: {e}", exc_info=True)
            # If Pub/Sub fails, consider marking the Firestore task as failed or retrying.
            # For simplicity, we'll just re-raise for now.
            raise

        return task_id

    async def _monitor_distributed_tasks(self):
        """
        Background task to periodically check for stale or failed tasks in Firestore
        and re-distribute them if necessary.
        """
        while self.is_running:
            logger.info("Orchestrator: Monitoring distributed tasks for stale entries.")
            try:
                # Query for tasks that are 'pending' or 'assigned' and haven't been updated
                # for a certain period (stale_task_timeout_minutes).
                # Note: Firestore queries on timestamps can be tricky with local time vs server time.
                # Using server_timestamp for 'created_at' and 'last_updated_at' helps.
                
                # Fetch all pending/assigned tasks for now and filter in-memory for simplicity
                # For large scale, consider more precise Firestore queries or Cloud Functions triggers
                tasks_ref = db.collection(TASK_COLLECTION_NAME)
                
                # Get tasks that are 'pending' or 'assigned'
                query_pending = tasks_ref.where("status", "==", "pending")
                query_assigned = tasks_ref.where("status", "==", "assigned")

                pending_tasks = await asyncio.to_thread(query_pending.get)
                assigned_tasks = await asyncio.to_thread(query_assigned.get)

                stale_tasks_to_requeue = []
                now = datetime.now()

                for doc in pending_tasks:
                    task = doc.to_dict()
                    # Check if pending task has been pending for too long (e.g., agent never picked it up)
                    created_at_dt = task.get("created_at")
                    if created_at_dt and isinstance(created_at_dt, datetime):
                        if (now - created_at_dt) > timedelta(minutes=self.stale_task_timeout_minutes):
                            logger.warning(f"Orchestrator: Found stale pending task: {task['id']}. Requeuing.")
                            stale_tasks_to_requeue.append(task)

                for doc in assigned_tasks:
                    task = doc.to_dict()
                    # Check if assigned task hasn't been updated for too long (e.g., agent crashed)
                    last_updated_at_dt = task.get("last_updated_at")
                    if last_updated_at_dt and isinstance(last_updated_at_dt, datetime):
                        if (now - last_updated_at_dt) > timedelta(minutes=self.stale_task_timeout_minutes):
                            logger.warning(f"Orchestrator: Found stale assigned task: {task['id']} (assigned to {task['assigned_to']}). Requeuing.")
                            stale_tasks_to_requeue.append(task)
                
                for task in stale_tasks_to_requeue:
                    # Increment retry count and re-publish
                    new_retries = task.get("retries", 0) + 1
                    await db.collection(TASK_COLLECTION_NAME).document(task['id']).update({
                        "status": "pending", # Reset to pending
                        "assigned_to": None,
                        "retries": new_retries,
                        "last_updated_at": firestore.SERVER_TIMESTAMP,
                        "orchestrator_notes": firestore.ArrayUnion([f"Requeued at {datetime.now().isoformat()} (retries: {new_retries})"])
                    })
                    logger.info(f"Orchestrator: Requeued task '{task['id']}'. Retries: {new_retries}")
                    
                    # Re-publish to Pub/Sub
                    message_data = json.dumps(task).encode("utf-8")
                    topic_path = publisher.topic_path(GCP_PROJECT_ID, DISTRIBUTED_TASKS_TOPIC_ID)
                    future = publisher.publish(topic_path, message_data, task_id=task['id'])
                    await asyncio.to_thread(future.result)
                    logger.info(f"Orchestrator: Re-published task '{task['id']}' to Pub/Sub.")

            except Exception as e:
                logger.error(f"Orchestrator: Error during task monitoring: {e}", exc_info=True)
            
            await asyncio.sleep(self.task_monitor_interval_seconds)

# --- FastAPI Integration (for triggering tasks manually or via other services) ---
from fastapi import FastAPI, BackgroundTasks, HTTPException

orchestrator_app = FastAPI(title="MPETI Orchestrator Service")
orchestrator_instance: Optional[MpetiOrchestrator] = None

@orchestrator_app.on_event("startup")
async def startup_event():
    global orchestrator_instance
    orchestrator_instance = MpetiOrchestrator()
    asyncio.create_task(orchestrator_instance.start())
    logger.info("MPETI Orchestrator service started.")

@orchestrator_app.on_event("shutdown")
async def shutdown_event():
    if orchestrator_instance:
        await orchestrator_instance.stop()
    logger.info("MPETI Orchestrator service stopped.")

@orchestrator_app.post("/orchestrate/create_task")
async def create_orchestrated_task(
    task_type: str, 
    description: str, 
    details: Dict[str, Any] = {}
):
    """
    API endpoint to create and distribute a new task via the orchestrator.
    """
    if not orchestrator_instance or not orchestrator_instance.is_running:
        raise HTTPException(status_code=503, detail="Orchestrator is not running.")
    
    try:
        task_id = await orchestrator_instance.create_and_distribute_task(task_type, description, details)
        return {"status": "success", "task_id": task_id, "message": "Task created and distributed."}
    except Exception as e:
        logger.error(f"Failed to create and distribute task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create and distribute task: {e}")

@orchestrator_app.get("/orchestrate/status")
async def get_orchestrator_status():
    """Returns the current status of the orchestrator."""
    if not orchestrator_instance:
        raise HTTPException(status_code=503, detail="Orchestrator instance not yet created.")
    
    return {
        "is_running": orchestrator_instance.is_running,
        "task_monitor_interval_seconds": orchestrator_instance.task_monitor_interval_seconds,
        "stale_task_timeout_minutes": orchestrator_instance.stale_task_timeout_minutes
    }

# The __main__ block for local development is removed for production readiness.
# In a real deployment, Gunicorn will be used as the entrypoint via a Dockerfile.
