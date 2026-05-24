import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.database import SessionLocal, Vote

logger = logging.getLogger(__name__)

class VoteHistoryLedger:
    """Simple synchronous ledger for storing and querying votes."""
    def __init__(self):
        logger.info("VoteHistoryLedger initialized (synchronous DB-backed).")

    def record_vote(self, agent_id: str, proposal_id: str, vote: str, reasoning: str = "", confidence: float = 0.0, vote_id: Optional[str] = None) -> str:
        """Stores a vote and returns the vote_id."""
        vid = vote_id or str(uuid.uuid4())
        with SessionLocal() as db:
            try:
                v = Vote(
                    vote_id=vid,
                    agent_id=agent_id,
                    proposal_id=proposal_id,
                    vote=vote,
                    confidence=confidence,
                    reasoning=reasoning,
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(v)
                db.commit()
                logger.info(f"Recorded vote {vid} for agent {agent_id} on proposal {proposal_id}")
                return vid
            except Exception as e:
                logger.error(f"Failed to record vote for {agent_id}: {e}", exc_info=True)
                db.rollback()
                raise

    def get_last_votes(self, agent_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        with SessionLocal() as db:
            try:
                rows = db.query(Vote).filter(Vote.agent_id == agent_id).order_by(Vote.timestamp.desc()).limit(limit).all()
                return [
                    {
                        "vote_id": r.vote_id,
                        "agent_id": r.agent_id,
                        "proposal_id": r.proposal_id,
                        "vote": r.vote,
                        "confidence": float(r.confidence) if r.confidence is not None else 0.0,  # type: ignore
                        "reasoning": r.reasoning,
                        "timestamp": r.timestamp.isoformat() if r.timestamp is not None else None  # type: ignore
                    }
                    for r in rows
                ]
            except Exception as e:
                logger.error(f"Failed to fetch votes for {agent_id}: {e}", exc_info=True)
                return []

    def get_vote(self, vote_id: str) -> Optional[Dict[str, Any]]:
        with SessionLocal() as db:
            try:
                r = db.query(Vote).filter(Vote.vote_id == vote_id).first()
                if not r:
                    return None
                return {
                    "vote_id": r.vote_id,
                    "agent_id": r.agent_id,
                    "proposal_id": r.proposal_id,
                    "vote": r.vote,
                    "confidence": float(r.confidence) if r.confidence is not None else 0.0,  # type: ignore
                    "reasoning": r.reasoning,
                    "timestamp": r.timestamp.isoformat() if r.timestamp is not None else None  # type: ignore
                }
            except Exception as e:
                logger.error(f"Failed to fetch vote {vote_id}: {e}", exc_info=True)
                return None