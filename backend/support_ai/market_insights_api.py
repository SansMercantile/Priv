# backend/support_ai/market_insights_api.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

# Import Firestore modules
try:
    from firebase_admin import firestore
    from firebase_admin import auth as firebase_auth  # For user authentication context
    FIREBASE_AVAILABLE = True
    FirestoreClient = firestore.Client
except ImportError:
    firestore = None
    firebase_auth = None
    FIREBASE_AVAILABLE = False
    FirestoreClient = Any  # Use Any when firestore is not available
    logger.warning("Firebase Admin SDK not available. Using local fallback.")

router = APIRouter()

# --- Pydantic Models for Market Insights Data ---

class TechnicalAnalysisInsight(BaseModel):
    """Details for technical analysis insights."""
    chart_image_url: Optional[str] = Field(None, description="URL to a generated chart image (e.g., in GCS).")
    patterns_identified: List[str] = Field(default_factory=list, description="List of identified chart patterns (e.g., 'Head and Shoulders', 'Double Top').")
    trend_lines: List[Dict[str, Any]] = Field(default_factory=list, description="Details of identified trend lines.")
    indicators_signals: List[Dict[str, Any]] = Field(default_factory=list, description="Signals from technical indicators (e.g., RSI, MACD).")
    summary: str = Field(..., description="Narrative summary of technical analysis.")

class FundamentalAnalysisInsight(BaseModel):
    """Details for fundamental analysis insights."""
    news_headlines: List[str] = Field(default_factory=list, description="Relevant news headlines.")
    news_sentiment: str = Field(..., description="Overall sentiment derived from news (e.g., 'positive', 'negative', 'neutral').")
    economic_events: List[Dict[str, Any]] = Field(default_factory=list, description="Upcoming or recent economic events.")
    explanation: str = Field(..., description="Detailed explanation of fundamental impact.")

class AgentSentiment(BaseModel):
    """Sentiment and input from a specific expert agent."""
    agent_id: str = Field(..., description="ID of the expert agent.")
    sentiment: str = Field(..., description="Agent's sentiment (e.g., 'bullish', 'bearish', 'neutral').")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Agent's confidence in its sentiment.")
    rationale: Optional[str] = Field(None, description="Brief rationale for the agent's sentiment.")

class AgentVote(BaseModel):
    """A single agent's vote on a trade opportunity."""
    agent_id: str = Field(..., description="ID of the voting agent.")
    vote: str = Field(..., description="Agent's vote (e.g., 'yes', 'no', 'abstain').")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Agent's confidence in its vote.")
    timestamp: datetime = Field(default_factory=datetime.now, description="Time of the vote.")

class ArbitrationalOutcome(BaseModel):
    """Outcome of the multi-agent arbitration."""
    outcome: str = Field(..., description="Final arbitrated decision (e.g., 'Proceed with Trade', 'Hold', 'Reject').")
    consensus_score: float = Field(..., ge=0.0, le=1.0, description="Consensus score from arbitration.")
    vote_tally: Dict[str, int] = Field(default_factory=dict, description="Tally of votes (e.g., {'yes': 5, 'no': 2}).")
    arbitrator_notes: Optional[str] = Field(None, description="Notes from the arbitration engine.")

class MarketInsight(BaseModel):
    """Comprehensive Priv Market Insight for a given symbol and timeframe."""
    insight_id: str = Field(..., description="Unique ID for this market insight.")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of when this insight was generated.")
    symbol: str = Field(..., description="The financial instrument (e.g., 'EURUSD', 'SPY').")
    timeframe: str = Field(..., description="The analysis timeframe (e.g., 'H1', 'D1').")
    
    technical_analysis: Optional[TechnicalAnalysisInsight] = Field(None, description="Detailed technical analysis.")
    fundamental_analysis: Optional[FundamentalAnalysisInsight] = Field(None, description="Detailed fundamental analysis.")
    
    agent_inputs: List[AgentSentiment] = Field(default_factory=list, description="Inputs and sentiments from various expert agents.")
    
    arbitration_outcome: Optional[ArbitrationalOutcome] = Field(None, description="Outcome of the multi-agent arbitration for a potential trade.")
    
    overall_summary: str = Field(..., description="Overall summary and Priv's market prediction.")
    # Add other relevant fields as needed, e.g., related trade proposals, risk assessment summary

# --- Firestore Collection Name ---
MARKET_INSIGHTS_COLLECTION = "market_insights"

# --- Firestore Dependency for FastAPI ---
_db_instance = None
_app_id_instance = None

def initialize_firestore_market_insights_api(db_instance, app_id_instance):
    """Initializes the Firestore client for the market_insights_api module."""
    global _db_instance, _app_id_instance
    _db_instance = db_instance
    _app_id_instance = app_id_instance
    logger.info("MarketInsightsAPI: Firestore client initialized.")

def get_firestore_db():
    """Dependency injector for Firestore database client."""
    if _db_instance is None:
        raise HTTPException(status_code=500, detail="Firestore database not initialized.")
    return _db_instance

def get_app_id():
    """Dependency injector for app ID."""
    if _app_id_instance is None:
        raise HTTPException(status_code=500, detail="App ID not initialized.")
    return _app_id_instance

# --- Dummy User Authentication (for development/testing without full Firebase Auth) ---
class CurrentUser:
    def __init__(self, uid: str):
        self.uid = uid

def get_current_user_dummy():
    """
    Dummy dependency for current user. In a real app, this would integrate with Firebase Auth.
    """
    return CurrentUser(uid="default-test-user-id")


@router.post("/insights/create", response_model=MarketInsight)
async def create_market_insight(
    insight: MarketInsight,
    db: FirestoreClient = Depends(get_firestore_db),
    app_id: str = Depends(get_app_id),
    current_user: CurrentUser = Depends(get_current_user_dummy) # User context for data ownership/access
):
    """
    Creates a new market insight entry in Firestore.
    """
    # Insights are often public or shared, but for this example, we'll put them under public data.
    collection_path = f"artifacts/{app_id}/public/data/{MARKET_INSIGHTS_COLLECTION}"
    
    try:
        # Use add() for auto-generated ID, or set() with insight.insight_id if you generate it beforehand
        doc_ref = await db.collection(collection_path).add(insight.model_dump())
        insight.insight_id = doc_ref.id # Update the Pydantic model with the Firestore ID
        logger.info(f"MarketInsightsAPI: Created new insight for {insight.symbol} (ID: {insight.insight_id}).")
        return insight
    except Exception as e:
        logger.error(f"MarketInsightsAPI: Failed to create market insight: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create insight: {e}")

@router.get("/insights/{symbol}/{timeframe}", response_model=List[MarketInsight])
async def get_market_insights(
    symbol: str,
    timeframe: str,
    limit: int = 10,
    db: FirestoreClient = Depends(get_firestore_db),
    app_id: str = Depends(get_app_id)
):
    """
    Retrieves the latest market insights for a given symbol and timeframe from Firestore.
    """
    collection_path = f"artifacts/{app_id}/public/data/{MARKET_INSIGHTS_COLLECTION}"
    
    try:
        query = db.collection(collection_path).where("symbol", "==", symbol).where("timeframe", "==", timeframe).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        docs = await query.get()
        
        insights = []
        for doc in docs:
            try:
                insight_data = doc.to_dict()
                # Convert Firestore Timestamps to datetime objects if necessary
                if 'timestamp' in insight_data and hasattr(insight_data['timestamp'], 'toDate'):
                    insight_data['timestamp'] = insight_data['timestamp'].toDate()
                insights.append(MarketInsight(**insight_data))
            except Exception as e:
                logger.warning(f"MarketInsightsAPI: Skipping malformed insight document {doc.id}: {e}")
        
        logger.info(f"MarketInsightsAPI: Retrieved {len(insights)} insights for {symbol} on {timeframe}.")
        return insights
    except Exception as e:
        logger.error(f"MarketInsightsAPI: Failed to retrieve market insights for {symbol}/{timeframe}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve insights: {e}")

@router.get("/insights/latest", response_model=Optional[MarketInsight])
async def get_latest_market_insight(
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    db: FirestoreClient = Depends(get_firestore_db),
    app_id: str = Depends(get_app_id)
):
    """
    Retrieves the single latest market insight (optionally filtered by symbol/timeframe).
    """
    collection_path = f"artifacts/{app_id}/public/data/{MARKET_INSIGHTS_COLLECTION}"
    
    try:
        query = db.collection(collection_path).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1)
        if symbol:
            query = query.where("symbol", "==", symbol)
        if timeframe:
            query = query.where("timeframe", "==", timeframe)

        docs = await query.get()
        
        if docs:
            doc = docs[0]
            insight_data = doc.to_dict()
            if 'timestamp' in insight_data and hasattr(insight_data['timestamp'], 'toDate'):
                insight_data['timestamp'] = insight_data['timestamp'].toDate()
            logger.info(f"MarketInsightsAPI: Retrieved latest insight (ID: {doc.id}).")
            return MarketInsight(**insight_data)
        else:
            logger.info("MarketInsightsAPI: No latest insight found.")
            return None
    except Exception as e:
        logger.error(f"MarketInsightsAPI: Failed to retrieve latest market insight: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve latest insight: {e}")

