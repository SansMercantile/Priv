import asyncio
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from collections import defaultdict, deque

from .priv_agent import PrivAgent
from .agent_reputation_ledger import AgentReputationLedger
# Make agi_core optional - it may not be available in all deployments
try:
    from shared_resource.agi_core.knowledge_sharing_protocol import KnowledgeSharingProtocol
    from shared_resource.agi_core.collective_decision_engine import CollectiveDecisionEngine
    from shared_resource.agi_core.swarm_intelligence import SwarmIntelligence
    AGI_CORE_AVAILABLE = True
except ImportError:
    AGI_CORE_AVAILABLE = False
    class KnowledgeSharingProtocol:
        async def initialize(self, agents): pass
        async def shutdown(self): pass
    class CollectiveDecisionEngine:
        async def initialize_session(self, session): pass
        async def make_collective_decision(self, decision_id, context, participants, urgency):
            return {
                "decision_id": decision_id,
                "status": "approved",
                "consensus_score": 1.0,
                "selected_option": "default",
                "resolution": "approved by fallback collective engine",
                "voted_option": "default"
            }
        async def shutdown(self): pass
    class SwarmIntelligence:
        async def initialize(self, agents): pass
        async def shutdown(self): pass
    logger = logging.getLogger(__name__)
    logger.warning("agi_core not available. Collaborative intelligence will use basic algorithms.")

logger = logging.getLogger(__name__)

class CollaborationMode(str, Enum):
    COMPETITIVE = "competitive"
    COOPERATIVE = "cooperative"
    HYBRID = "hybrid"
    EMERGENCY = "emergency"

class IntelligenceLevel(str, Enum):
    INDIVIDUAL = "individual"
    GROUP = "group"
    COLLECTIVE = "collective"
    SWARM = "swarm"

@dataclass
class CollaborationSession:
    session_id: str
    participants: Set[str]
    objective: str
    mode: CollaborationMode
    start_time: datetime
    end_time: Optional[datetime] = None
    outcomes: List[Dict[str, Any]] = field(default_factory=list)
    knowledge_shared: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class SharedKnowledge:
    knowledge_id: str
    source_agent: str
    knowledge_type: str
    content: Dict[str, Any]
    confidence: float
    timestamp: datetime
    access_level: str = "public"
    usage_count: int = 0
    effectiveness_score: float = 0.0

class CollaborativeIntelligence:
    """Advanced collaborative intelligence system for multi-agent coordination"""
    
    def __init__(self):
        # Core components
        self.knowledge_sharing = KnowledgeSharingProtocol()
        self.decision_engine = CollectiveDecisionEngine()
        self.swarm_intelligence = SwarmIntelligence()
        
        # Agent management
        self.agents: Dict[str, PrivAgent] = {}
        self.agent_capabilities: Dict[str, Set[str]] = {}
        self.agent_specializations: Dict[str, List[str]] = {}
        
        # Collaboration state
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.collaboration_history: List[CollaborationSession] = []
        self.shared_knowledge_base: Dict[str, SharedKnowledge] = {}
        
        # Intelligence networks
        self.expertise_networks: Dict[str, Set[str]] = {}
        self.collaboration_networks: Dict[str, Dict[str, float]] = {}
        self.knowledge_networks: Dict[str, Set[str]] = {}
        
        # Learning and adaptation
        self.collaboration_patterns: Dict[str, Dict[str, Any]] = {}
        self.success_patterns: List[Dict[str, Any]] = []
        self.failure_patterns: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.collective_performance_history: deque = deque(maxlen=1000)
        self.collaboration_effectiveness: Dict[str, float] = {}
        
        logger.info("Collaborative Intelligence system initialized")
    
    async def initialize(self, agents: Dict[str, PrivAgent]):
        """Initialize the collaborative intelligence system with agents"""
        
        self.agents = agents
        
        # Analyze agent capabilities
        await self._analyze_agent_capabilities()
        
        # Build expertise networks
        await self._build_expertise_networks()
        
        # Initialize knowledge sharing
        await self.knowledge_sharing.initialize(agents)
        
        # Initialize swarm intelligence
        await self.swarm_intelligence.initialize(agents)
        
        # Start background processes
        asyncio.create_task(self._collaboration_optimization_loop())
        asyncio.create_task(self._knowledge_maintenance_loop())
        asyncio.create_task(self._pattern_learning_loop())
        
        logger.info(f"Collaborative Intelligence initialized with {len(agents)} agents")
    
    async def _analyze_agent_capabilities(self):
        """Analyze capabilities of each agent"""
        
        for agent_id, agent in self.agents.items():
            capabilities = set()
            specializations = []
            
            # Extract from persona
            persona = getattr(agent, 'persona', {})
            focus = persona.get('focus', '')
            
            # Map focus to capabilities
            capability_mapping = {
                'technical_analysis': {'chart_analysis', 'indicator_calculation', 'pattern_recognition'},
                'risk_management': {'risk_assessment', 'position_sizing', 'stop_loss_management'},
                'compliance': {'regulatory_check', 'ethical_assessment', 'legal_validation'},
                'economics': {'macro_analysis', 'fundamental_analysis', 'economic_forecasting'},
                'sentiment': {'sentiment_analysis', 'social_media_monitoring', 'news_analysis'},
                'execution': {'order_management', 'trade_execution', 'slippage_optimization'},
                'portfolio': {'portfolio_optimization', 'asset_allocation', 'rebalancing'},
                'machine_learning': {'model_training', 'prediction', 'feature_engineering'},
                'research': {'data_analysis', 'report_generation', 'market_research'},
                'options': {'options_pricing', 'volatility_analysis', 'greeks_calculation'},
                'forex': {'currency_analysis', 'carry_trade', 'cross_rate_analysis'},
            }
            
            if focus in capability_mapping:
                capabilities.update(capability_mapping[focus])
                specializations.append(focus)
            
            # Add general capabilities
            capabilities.update({'communication', 'data_processing', 'decision_making'})
            
            self.agent_capabilities[agent_id] = capabilities
            self.agent_specializations[agent_id] = specializations
    
    async def _build_expertise_networks(self):
        """Build networks of agents based on expertise"""
        
        # Group agents by expertise areas
        expertise_groups = defaultdict(set)
        
        for agent_id, specializations in self.agent_specializations.items():
            for specialization in specializations:
                expertise_groups[specialization].add(agent_id)
        
        self.expertise_networks = dict(expertise_groups)
        
        # Build collaboration strength matrix
        for agent_id in self.agents:
            self.collaboration_networks[agent_id] = {}
            
            for other_agent_id in self.agents:
                if agent_id != other_agent_id:
                    # Calculate collaboration strength based on complementary capabilities
                    strength = self._calculate_collaboration_strength(agent_id, other_agent_id)
                    self.collaboration_networks[agent_id][other_agent_id] = strength
    
    def _calculate_collaboration_strength(self, agent1_id: str, agent2_id: str) -> float:
        """Calculate collaboration strength between two agents"""
        
        caps1 = self.agent_capabilities.get(agent1_id, set())
        caps2 = self.agent_capabilities.get(agent2_id, set())
        
        # Complementary capabilities (different but related)
        complementary = len(caps1.symmetric_difference(caps2))
        
        # Overlapping capabilities (shared expertise)
        overlap = len(caps1.intersection(caps2))
        
        # Specialization compatibility
        spec1 = set(self.agent_specializations.get(agent1_id, []))
        spec2 = set(self.agent_specializations.get(agent2_id, []))
        spec_compatibility = len(spec1.union(spec2)) - len(spec1.intersection(spec2))
        
        # Calculate strength (higher for complementary, moderate for overlap)
        strength = (complementary * 0.6 + overlap * 0.3 + spec_compatibility * 0.1) / 10
        
        return min(max(strength, 0.0), 1.0)
    
    async def initiate_collaboration(
        self,
        objective: str,
        required_capabilities: List[str],
        mode: CollaborationMode = CollaborationMode.COOPERATIVE,
        max_participants: int = 5
    ) -> str:
        """Initiate a collaboration session"""
        
        # Find suitable agents
        suitable_agents = await self._find_suitable_agents(required_capabilities, max_participants)
        
        if len(suitable_agents) < 2:
            raise ValueError("Insufficient suitable agents for collaboration")
        
        # Create collaboration session
        session_id = f"collab_{datetime.utcnow().timestamp()}"
        session = CollaborationSession(
            session_id=session_id,
            participants=set(suitable_agents),
            objective=objective,
            mode=mode,
            start_time=datetime.utcnow()
        )
        
        self.active_sessions[session_id] = session
        
        # Initialize collaboration
        await self._setup_collaboration_session(session)
        
        logger.info(f"Initiated collaboration session {session_id} with {len(suitable_agents)} agents")
        return session_id
    
    async def _find_suitable_agents(
        self, 
        required_capabilities: List[str], 
        max_participants: int
    ) -> List[str]:
        """Find agents suitable for collaboration based on capabilities"""
        
        # Score agents based on capability match
        agent_scores = {}
        
        for agent_id, capabilities in self.agent_capabilities.items():
            # Calculate capability match score
            matched_caps = len(set(required_capabilities).intersection(capabilities))
            total_caps = len(capabilities)
            
            # Capability coverage score
            coverage_score = matched_caps / len(required_capabilities) if required_capabilities else 0
            
            # Capability depth score (more capabilities = more versatile)
            depth_score = min(total_caps / 10, 1.0)
            
            # Reputation score (from agent metrics if available)
            reputation_score = 0.5  # Default, would get from reputation system
            
            # Combined score
            agent_scores[agent_id] = (coverage_score * 0.5 + depth_score * 0.3 + reputation_score * 0.2)
        
        # Sort by score and select top agents
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        selected_agents = [agent_id for agent_id, score in sorted_agents[:max_participants] if score > 0.3]
        
        return selected_agents
    
    async def _setup_collaboration_session(self, session: CollaborationSession):
        """Setup a collaboration session"""
        
        # Create shared workspace
        workspace = await self._create_shared_workspace(session.session_id)
        
        # Establish communication channels
        await self._establish_communication_channels(session)
        
        # Share relevant knowledge
        await self._share_relevant_knowledge(session)
        
        # Initialize collective decision making
        await self.decision_engine.initialize_session(session)
        
        # Start collaboration monitoring
        asyncio.create_task(self._monitor_collaboration_session(session.session_id))
    
    async def _create_shared_workspace(self, session_id: str) -> Dict[str, Any]:
        """Create a shared workspace for collaboration"""
        
        workspace = {
            "session_id": session_id,
            "shared_data": {},
            "shared_models": {},
            "shared_insights": [],
            "decision_log": [],
            "communication_log": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store workspace (in practice, this would be in a shared database)
        return workspace
    
    async def _establish_communication_channels(self, session: CollaborationSession):
        """Establish communication channels for collaboration"""
        
        # Create dedicated topics for this session
        session_topics = [
            f"collab_{session.session_id}_general",
            f"collab_{session.session_id}_decisions",
            f"collab_{session.session_id}_knowledge",
            f"collab_{session.session_id}_coordination"
        ]
        
        # Notify participants about the session
        for participant in session.participants:
            collaboration_invite = {
                "session_id": session.session_id,
                "objective": session.objective,
                "mode": session.mode.value,
                "participants": list(session.participants),
                "communication_topics": session_topics,
                "start_time": session.start_time.isoformat()
            }
            
            # Send invite (in practice, would use message broker)
            logger.info(f"Sending collaboration invite to {participant}")
    
    async def _share_relevant_knowledge(self, session: CollaborationSession):
        """Share relevant knowledge for the collaboration"""
        
        # Find relevant knowledge for the session objective
        relevant_knowledge = []
        
        for knowledge_id, knowledge in self.shared_knowledge_base.items():
            # Check if knowledge is relevant to the objective
            if self._is_knowledge_relevant(knowledge, session.objective):
                relevant_knowledge.append(knowledge)
        
        # Share knowledge with participants
        for knowledge in relevant_knowledge:
            knowledge_share = {
                "session_id": session.session_id,
                "knowledge_id": knowledge.knowledge_id,
                "source_agent": knowledge.source_agent,
                "knowledge_type": knowledge.knowledge_type,
                "content": knowledge.content,
                "confidence": knowledge.confidence
            }
            
            session.knowledge_shared.append(knowledge_share)
    
    def _is_knowledge_relevant(self, knowledge: SharedKnowledge, objective: str) -> bool:
        """Check if knowledge is relevant to an objective"""
        
        # Simple keyword matching (in practice, would use more sophisticated NLP)
        objective_keywords = objective.lower().split()
        knowledge_text = json.dumps(knowledge.content).lower()
        
        relevance_score = sum(1 for keyword in objective_keywords if keyword in knowledge_text)
        return relevance_score > 0
    
    async def share_knowledge(
        self,
        source_agent: str,
        knowledge_type: str,
        content: Dict[str, Any],
        confidence: float,
        access_level: str = "public"
    ) -> str:
        """Share knowledge in the collaborative system"""
        
        knowledge_id = f"knowledge_{datetime.utcnow().timestamp()}"
        
        knowledge = SharedKnowledge(
            knowledge_id=knowledge_id,
            source_agent=source_agent,
            knowledge_type=knowledge_type,
            content=content,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            access_level=access_level
        )
        
        self.shared_knowledge_base[knowledge_id] = knowledge
        
        # Update knowledge networks
        if source_agent not in self.knowledge_networks:
            self.knowledge_networks[source_agent] = set()
        
        # Notify relevant agents about new knowledge
        await self._notify_knowledge_sharing(knowledge)
        
        logger.info(f"Knowledge shared by {source_agent}: {knowledge_type}")
        return knowledge_id
    
    async def _notify_knowledge_sharing(self, knowledge: SharedKnowledge):
        """Notify relevant agents about new shared knowledge"""
        
        # Find agents who might be interested in this knowledge
        interested_agents = []
        
        for agent_id, capabilities in self.agent_capabilities.items():
            if agent_id != knowledge.source_agent:
                # Check if agent's capabilities align with knowledge type
                if self._is_agent_interested_in_knowledge(capabilities, knowledge):
                    interested_agents.append(agent_id)
        
        # Send notifications
        for agent_id in interested_agents:
            notification = {
                "type": "knowledge_available",
                "knowledge_id": knowledge.knowledge_id,
                "source_agent": knowledge.source_agent,
                "knowledge_type": knowledge.knowledge_type,
                "confidence": knowledge.confidence,
                "timestamp": knowledge.timestamp.isoformat()
            }
            
            # Send notification (in practice, would use message broker)
            logger.debug(f"Notifying {agent_id} about new knowledge: {knowledge.knowledge_type}")
    
    def _is_agent_interested_in_knowledge(
        self, 
        agent_capabilities: Set[str], 
        knowledge: SharedKnowledge
    ) -> bool:
        """Check if an agent would be interested in specific knowledge"""
        
        # Map knowledge types to relevant capabilities
        knowledge_capability_map = {
            'market_analysis': {'chart_analysis', 'fundamental_analysis', 'sentiment_analysis'},
            'risk_assessment': {'risk_assessment', 'position_sizing'},
            'technical_signal': {'chart_analysis', 'indicator_calculation'},
            'economic_insight': {'macro_analysis', 'economic_forecasting'},
            'compliance_rule': {'regulatory_check', 'legal_validation'},
            'trading_strategy': {'decision_making', 'trade_execution'},
        }
        
        relevant_capabilities = knowledge_capability_map.get(knowledge.knowledge_type, set())
        return len(agent_capabilities.intersection(relevant_capabilities)) > 0
    
    async def request_collective_decision(
        self,
        decision_context: Dict[str, Any],
        required_expertise: List[str],
        urgency: str = "normal"
    ) -> Dict[str, Any]:
        """Request a collective decision from relevant agents"""
        
        # Find expert agents
        expert_agents = []
        for expertise in required_expertise:
            experts = self.expertise_networks.get(expertise, set())
            expert_agents.extend(experts)
        
        expert_agents = list(set(expert_agents))  # Remove duplicates
        
        if not expert_agents:
            raise ValueError("No expert agents found for required expertise")
        
        # Create decision session
        decision_id = f"decision_{datetime.utcnow().timestamp()}"
        
        # Use collective decision engine
        decision_result = await self.decision_engine.make_collective_decision(
            decision_id=decision_id,
            context=decision_context,
            participants=expert_agents,
            urgency=urgency
        )
        
        return decision_result
    
    async def _collaboration_optimization_loop(self):
        """Continuously optimize collaboration patterns"""
        
        while True:
            try:
                await self._analyze_collaboration_patterns()
                await self._optimize_agent_groupings()
                await self._update_collaboration_networks()
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in collaboration optimization: {e}")
                await asyncio.sleep(300)
    
    async def _analyze_collaboration_patterns(self):
        """Analyze patterns in successful collaborations"""
        
        # Analyze completed sessions
        completed_sessions = [s for s in self.collaboration_history if s.end_time is not None]
        
        if len(completed_sessions) < 5:
            return  # Need more data
        
        # Identify successful patterns
        successful_sessions = [
            s for s in completed_sessions 
            if s.performance_metrics.get('success_score', 0) > 0.7
        ]
        
        # Extract patterns
        for session in successful_sessions:
            pattern = {
                'participant_count': len(session.participants),
                'participant_types': [
                    self.agent_specializations.get(p, ['unknown'])[0] 
                    for p in session.participants
                ],
                'collaboration_mode': session.mode.value,
                'objective_type': self._categorize_objective(session.objective),
                'duration': (session.end_time - session.start_time).total_seconds(),
                'success_score': session.performance_metrics.get('success_score', 0)
            }
            
            pattern_key = f"{pattern['objective_type']}_{pattern['collaboration_mode']}"
            if pattern_key not in self.collaboration_patterns:
                self.collaboration_patterns[pattern_key] = []
            
            self.collaboration_patterns[pattern_key].append(pattern)
    
    def _categorize_objective(self, objective: str) -> str:
        """Categorize an objective for pattern analysis"""
        
        objective_lower = objective.lower()
        
        if any(word in objective_lower for word in ['trade', 'buy', 'sell', 'position']):
            return 'trading'
        elif any(word in objective_lower for word in ['risk', 'exposure', 'hedge']):
            return 'risk_management'
        elif any(word in objective_lower for word in ['analyze', 'research', 'study']):
            return 'analysis'
        elif any(word in objective_lower for word in ['portfolio', 'allocation', 'rebalance']):
            return 'portfolio_management'
        else:
            return 'general'
    
    async def _monitor_collaboration_session(self, session_id: str):
        """Monitor an active collaboration session"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        start_time = datetime.utcnow()
        timeout = timedelta(hours=2)  # Maximum session duration
        
        while session_id in self.active_sessions:
            current_time = datetime.utcnow()
            
            # Check for timeout
            if current_time - start_time > timeout:
                await self._timeout_collaboration_session(session_id)
                break
            
            # Check session health
            await self._check_session_health(session_id)
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _timeout_collaboration_session(self, session_id: str):
        """Handle collaboration session timeout"""
        
        logger.warning(f"Collaboration session {session_id} timed out")
        
        session = self.active_sessions.get(session_id)
        if session:
            session.end_time = datetime.utcnow()
            session.performance_metrics['timeout'] = True
            session.performance_metrics['success_score'] = 0.3  # Low score for timeout
            
            # Move to history
            self.collaboration_history.append(session)
            del self.active_sessions[session_id]
    
    def get_collaboration_status(self) -> Dict[str, Any]:
        """Get current collaboration status"""
        
        return {
            "active_sessions": len(self.active_sessions),
            "total_agents": len(self.agents),
            "knowledge_base_size": len(self.shared_knowledge_base),
            "expertise_networks": {
                expertise: len(agents) 
                for expertise, agents in self.expertise_networks.items()
            },
            "collaboration_patterns": len(self.collaboration_patterns),
            "recent_performance": self._get_recent_performance_summary()
        }
    
    def _get_recent_performance_summary(self) -> Dict[str, Any]:
        """Get summary of recent collaboration performance"""
        
        recent_sessions = [
            s for s in self.collaboration_history 
            if s.end_time and s.end_time > datetime.utcnow() - timedelta(hours=24)
        ]
        
        if not recent_sessions:
            return {"status": "no_recent_data"}
        
        success_scores = [
            s.performance_metrics.get('success_score', 0) 
            for s in recent_sessions
        ]
        
        return {
            "sessions_count": len(recent_sessions),
            "average_success_score": sum(success_scores) / len(success_scores),
            "successful_sessions": len([s for s in success_scores if s > 0.7]),
            "average_duration": sum([
                (s.end_time - s.start_time).total_seconds() 
                for s in recent_sessions
            ]) / len(recent_sessions) / 60  # in minutes
        }
    
    async def shutdown(self):
        """Shutdown the collaborative intelligence system"""
        
        logger.info("Shutting down Collaborative Intelligence system...")
        
        # End all active sessions
        for session_id in list(self.active_sessions.keys()):
            await self._end_collaboration_session(session_id)
        
        # Shutdown components
        await self.knowledge_sharing.shutdown()
        await self.decision_engine.shutdown()
        await self.swarm_intelligence.shutdown()
        
        logger.info("Collaborative Intelligence system shut down")
    
    async def _end_collaboration_session(self, session_id: str):
        """End a collaboration session"""
        
        session = self.active_sessions.get(session_id)
        if session:
            session.end_time = datetime.utcnow()
            
            # Calculate final performance metrics
            await self._calculate_session_performance(session)
            
            # Move to history
            self.collaboration_history.append(session)
            del self.active_sessions[session_id]
            
            logger.info(f"Ended collaboration session {session_id}")
    
    async def _calculate_session_performance(self, session: CollaborationSession):
        """Calculate performance metrics for a completed session"""
        
        # Basic metrics
        duration = (session.end_time - session.start_time).total_seconds()
        knowledge_shared_count = len(session.knowledge_shared)
        outcomes_count = len(session.outcomes)
        
        # Calculate success score based on various factors
        success_score = 0.5  # Base score
        
        # Factor in knowledge sharing
        if knowledge_shared_count > 0:
            success_score += min(knowledge_shared_count * 0.1, 0.2)
        
        # Factor in outcomes
        if outcomes_count > 0:
            success_score += min(outcomes_count * 0.1, 0.2)
        
        # Factor in duration (not too short, not too long)
        optimal_duration = 1800  # 30 minutes
        duration_factor = 1 - abs(duration - optimal_duration) / optimal_duration
        success_score += duration_factor * 0.1
        
        session.performance_metrics.update({
            'success_score': min(max(success_score, 0.0), 1.0),
            'duration_seconds': duration,
            'knowledge_shared_count': knowledge_shared_count,
            'outcomes_count': outcomes_count,
            'participant_count': len(session.participants)
        })