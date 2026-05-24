import logging
from sqlalchemy.orm import Session # Correctly import Session for type hinting
from sqlalchemy import select # Still needed for query construction, even if executed synchronously
from typing import Dict, Any, List
# Removed asyncio import as methods are now synchronous

# --- Import the database session and Agent model ---
# MODIFIED: Import SessionLocal instead of AsyncSessionLocal
from backend.database import SessionLocal, Agent

logger = logging.getLogger(__name__)

# --- Configuration Constants ---
DEFAULT_STARTING_REPUTATION = 0.5
SCORE_SUCCESS_IMPACT = 0.05
SCORE_FAILURE_IMPACT = -0.075
SCORE_ETHICAL_VIOLATION_IMPACT = -0.2
SCORE_REGULATORY_VIOLATION_IMPACT = -0.3

class AgentReputationLedger:
    """
    Maintains agent reputations by interacting with a central SQL database.
    This version is scalable and suitable for a multi-agent system.
    """
    def __init__(self):
        logger.info("Priv's AgentReputationLedger initialized to use Cloud SQL (synchronous).")

    # MODIFIED: _get_or_create_agent is now synchronous
    def _get_or_create_agent(self, db: Session, agent_id: str, role: str = "default") -> Agent:
        """
        Retrieves an agent from the database or creates it if it doesn't exist.
        """
        # MODIFIED: Use db.query() for synchronous query
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        
        if not agent:
            logger.info(f"Agent '{agent_id}' not found in ledger. Creating with default reputation.")
            agent = Agent(
                agent_id=agent_id,
                role=role,
                reputation_score=DEFAULT_STARTING_REPUTATION
            )
            db.add(agent)
            db.commit() # No await for synchronous commit
            db.refresh(agent) # No await for synchronous refresh
        return agent

    # MODIFIED: record_trade_outcome is now synchronous
    def record_trade_outcome(self, agent_id: str, success: bool, details: Dict[str, Any]):
        """Records the outcome of a trade and updates the agent's reputation."""
        # Use SessionLocal to get a synchronous session
        with SessionLocal() as db:
            try:
                agent = self._get_or_create_agent(db, agent_id)
                score_impact = SCORE_SUCCESS_IMPACT if success else SCORE_FAILURE_IMPACT
                
                new_score = agent.reputation_score + score_impact
                agent.reputation_score = max(0.0, min(1.0, new_score)) # Clamp score between 0 and 1
                
                db.commit() # No await for synchronous commit
                logger.info(f"Recorded trade outcome for '{agent_id}'. New score: {agent.reputation_score:.3f}")
            except Exception as e:
                logger.error(f"Database error recording trade outcome for {agent_id}: {e}", exc_info=True)
                db.rollback() # No await for synchronous rollback

    # MODIFIED: record_compliance_check_outcome is now synchronous
    def record_compliance_check_outcome(self, agent_id: str, check_type: str, is_compliant: bool, violations: List[Dict[str, Any]]):
        """Records a compliance check outcome and applies a penalty if necessary."""
        if is_compliant:
            return # No reputation change for compliant actions

        with SessionLocal() as db:
            try:
                agent = self._get_or_create_agent(db, agent_id)
                score_impact = 0.0
                if check_type == "regulatory":
                    score_impact = SCORE_REGULATORY_VIOLATION_IMPACT
                    logger.critical(f"REGULATORY VIOLATION by '{agent_id}'. Applying penalty.")
                elif check_type == "ethical":
                    score_impact = SCORE_ETHICAL_VIOLATION_IMPACT
                    logger.critical(f"ETHICAL VIOLATION by '{agent_id}'. Applying penalty.")

                new_score = agent.reputation_score + score_impact
                agent.reputation_score = max(0.0, min(1.0, new_score))
                
                db.commit() # No await for synchronous commit
            except Exception as e:
                logger.error(f"Database error recording compliance outcome for {agent_id}: {e}", exc_info=True)
                db.rollback() # No await for synchronous rollback

    # MODIFIED: get_reputation_score is now synchronous
    def get_reputation_score(self, agent_id: str) -> float:
        """Retrieves the current reputation score for an agent from the database."""
        with SessionLocal() as db:
            agent = self._get_or_create_agent(db, agent_id)
            return agent.reputation_score

    async def get_reputation(self, agent_id: str) -> float:
        """Retrieve the current reputation score (async wrapper for compatibility)."""
        return self.get_reputation_score(agent_id)

    async def initialize(self) -> bool:
        """Initialize the reputation ledger (compatibility interface)."""
        return True

    async def update_reputation(self, agent_id: str, score: float, feedback: str) -> None:
        """Updates agent reputation based on custom score and feedback (compatibility interface)."""
        with SessionLocal() as db:
            try:
                agent = self._get_or_create_agent(db, agent_id)
                agent.reputation_score = max(0.0, min(1.0, score))
                db.commit()
                logger.info(f"Updated reputation for '{agent_id}' to {score:.3f} (Feedback: {feedback})")
            except Exception as e:
                logger.error(f"Database error updating reputation for {agent_id}: {e}", exc_info=True)
                db.rollback()

    # MODIFIED: get_all_agent_scores is now synchronous
    def get_all_agent_scores(self) -> Dict[str, float]:
        """Retrieves all agent scores from the database."""
        with SessionLocal() as db:
            # MODIFIED: Use db.query().all() for synchronous query
            agents = db.query(Agent).all()
            return {agent.agent_id: agent.reputation_score for agent in agents}

    # Removed the SessionLocal(self) method as it's no longer needed for external access
    # when the methods themselves manage their sessions.
