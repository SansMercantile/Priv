# backend/multi_agent/priv_agent_protocol.py

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime

class AgentType(str, Enum):
    NEWS_ANALYSIS = "news_analysis"
    COMPLIANCE = "compliance"
    ARBITRAGE = "arbitrage"
    ECONOMIC = "economic"
    EXECUTION = "execution"
    POLITICAL = "political"
    PORTFOLIO_MANAGER = "portfolio_manager"
    QUANTITATIVE = "quantitative"
    RISK = "risk"
    SENTIMENT = "sentiment"
    STRATEGIST = "strategist"
    TECHNICAL = "technical"
    COMMODITY = "commodity"
    FUTURES = "futures"
    CREDIT = "credit"
    LEGAL = "legal"
    AUDIT = "audit"
    AI_OPS = "ai_ops"
    RESEARCH = "research"
    FOMC = "fomc"
    YIELD_OPTIMIZER = "yield_optimizer"
    ALTERNATIVE_DATA = "alternative_data"
    SOCIAL_MEDIA = "social_media"
    TAX = "tax"
    ML = "ml"
    OPTIONS = "options"
    FOREX = "forex"
    SYNTHETIC_MARKETS = "synthetic_markets"
    SENSORY = "sensory"
    REGULATORY_ARBITER = "regulatory_arbiter"
    ETHICAL_ARBITER = "ethical_arbiter"
    ORCHESTRATOR = "orchestrator"
    IT = "it"
    ACCOUNTS = "accounts"
    DATA_ANALYST = "data_analyst"
    PATENT_RESEARCHER = "patent_researcher"
    HR = "hr"
    MARKETING = "marketing"
    INNOVATION = "innovation"
    SALES = "sales"
    CONTENT_EDITOR = "content_editor"
    ARTICLE_WRITER = "article_writer"
    DATA_SCRAPER = "data_scraper"
    GRAPHIC_DESIGN = "graphic_design"
    MARKET_RESEARCHER = "market_researcher"
    PUBLISHER = "publisher"
    SEO = "seo"
    CYBERSECURITY = "cybersecurity"
    PROJECT_MANAGEMENT = "project_management"
    BUSINESS_ANALYST = "business_analyst"
    DESIGN = "design"
    QUALITY_ASSURANCE = "quality_assurance"
    LEARNING_DEVELOPMENT = "learning_development"
    EVENT_PLANNING = "event_planning"
    SOCIAL_MEDIA_MANAGER = "social_media_manager"
    COPYWRITER = "copywriter"
    VIDEO_PRODUCTION = "video_production"

class AgentState(str, Enum):
    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    ERROR = "ERROR"
    SHUTDOWN = "SHUTDOWN"
    # Graceful shutdown state used by orchestrator stop sequences
    SHUTTING_DOWN = "SHUTTING_DOWN"

class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class DecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ResolutionType(str, Enum):
    STANDARD = "STANDARD"
    SYSTEM_HEALING = "SYSTEM_HEALING"

class MessageType(str, Enum):
    """Defines the types of messages agents can send and receive."""
    TRADE_PROPOSAL = "TRADE_PROPOSAL"
    ARBITRATION_VOTE = "ARBITRATION_VOTE"
    ARBITRATION_DECISION = "ARBITRATION_DECISION"
    DATA_INSIGHT = "DATA_INSIGHT"
    STATUS_UPDATE = "STATUS_UPDATE"
    SYSTEM_ALERT = "SYSTEM_ALERT"
    ERROR_NOTIFICATION = "ERROR_NOTIFICATION"
    USER_FEEDBACK = "USER_FEEDBACK"
    TASK = "TASK"
    DIRECTIVE = "DIRECTIVE"  # NEW: For C-Suite agents to issue commands
    RISK_ALERT = "RISK_ALERT"  # Risk violation alerts
    RISK_DASHBOARD_UPDATE = "RISK_DASHBOARD_UPDATE"  # Risk metrics dashboard updates

class AgentMessage(BaseModel):
    """Standard message format for inter-agent communication."""
    sender_id: str
    sender_type: str = "agent"  # default sender type
    recipient_id: str = ""  # default to empty recipient (broadcast/orchestrator)
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    priority: int = 1  # Optional priority field for routing/processing order


class TradeProposal(BaseModel):
    """Payload for a trade proposal message."""
    symbol: str
    action: TradeAction  # BUY, SELL, HOLD
    quantity: float
    order_type: str = "MARKET"
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    originating_agent_id: str

class ArbitrationVote(BaseModel):
    """Payload for an arbitration vote."""
    proposal_id: str
    vote: str  # "APPROVE", "REJECT", "ABSTAIN"
    reasoning: str
    voting_agent_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)

class ArbitrationDecision(BaseModel):
    """Payload for a final arbitration decision."""
    proposal_id: str
    decision_id: str
    status: DecisionStatus
    resolution_type: ResolutionType = ResolutionType.STANDARD
    summary: str
    trade_details: Dict[str, Any] = Field(default_factory=dict)
    winning_votes: List[ArbitrationVote]
    losing_votes: List[ArbitrationVote]
    reason: Optional[str] = None

class PrivAgentProtocol:
    """Protocol for inter-agent communication in PRIV system"""
    
    @staticmethod
    def create_message(message_type: MessageType, sender_id: str, recipient_id: str, 
                      payload: Dict[str, Any], sender_type: str = "", priority: int = 1) -> AgentMessage:
        """Create a standardized agent message"""
        return AgentMessage(
            message_type=message_type,
            sender_id=sender_id,
            sender_type=sender_type,
            recipient_id=recipient_id,
            payload=payload,
            priority=priority
        )
    
    @staticmethod
    def create_trade_proposal(proposer_id: str, symbol: str, action: TradeAction, 
                             quantity: int, price: float, reasoning: str, confidence: float) -> TradeProposal:
        """Create a standardized trade proposal"""
        return TradeProposal(
            proposer_id=proposer_id,
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            reasoning=reasoning,
            confidence=confidence
        )
    
    @staticmethod
    def create_arbitration_vote(agent_id: str, proposal_id: str, vote: str, 
                               reasoning: str, confidence: float) -> ArbitrationVote:
        """Create a standardized arbitration vote"""
        return ArbitrationVote(
            proposal_id=proposal_id,
            vote=vote,
            reasoning=reasoning,
            voting_agent_id=agent_id,
            confidence=confidence
        )

