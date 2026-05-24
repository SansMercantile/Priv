# priv/backend/multi_agent/departmental_orchestrator.py 
import asyncio
import logging
from typing import Dict, Any, List
from collections import deque
import json
import os
from backend.config import settings

project_id = settings.GCP_PROJECT_ID


from backend.multi_agent.priv_agent_protocol import AgentType, AgentMessage, TradeProposal, ArbitrationVote, ArbitrationDecision
from backend.multi_agent.message_broker_interface import MessageBrokerInterface, GoogleCloudPubSubBroker
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.agent_reputation_ledger import AgentReputationLedger
from backend.multi_agent.arbitration_engine import ArbitrationEngine
from backend.config import settings
# Import only departmental agents here
# Dynamically import all departmental agents to avoid circular dependencies
# Wrap all imports in try-except to handle missing dependencies gracefully
try:
    from brigit.multi_agents.it_agent import ITAgent
    from brigit.multi_agents.accounts_agent import AccountsAgent
    from brigit.multi_agents.data_analyst_agent import DataAnalystAgent
    from brigit.multi_agents.patent_researcher_agent import PatentResearcherAgent
    from brigit.multi_agents.hr_agent import HRAgent
    from brigit.multi_agents.marketing_agent import MarketingAgent
    from brigit.multi_agents.innovation_agent import InnovationAgent
    from brigit.multi_agents.sales_agent import SalesAgent
    from brigit.multi_agents.content_editor_agent import ContentEditorAgent
    from brigit.multi_agents.article_writer_agent import ArticleWriterAgent
    from brigit.multi_agents.data_scraper_agent import DataScraperAgent
    BRIGIT_CORE_AGENTS_AVAILABLE = True
except ImportError as e:
    ITAgent = None
    AccountsAgent = None
    DataAnalystAgent = None
    PatentResearcherAgent = None
    HRAgent = None
    MarketingAgent = None
    InnovationAgent = None
    SalesAgent = None
    ContentEditorAgent = None
    ArticleWriterAgent = None
    DataScraperAgent = None
    BRIGIT_CORE_AGENTS_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Brigit core agents not available: {e}. Departmental orchestrator will run without these agents.")
# Make brigit agents optional - they may not be available in all deployments
try:
    from brigit.multi_agents.it_and_infrastructure_agents.cybersecurity_agent import CyberSecurityAgent
    BRIGIT_AGENTS_AVAILABLE = True
except ImportError:
    BRIGIT_AGENTS_AVAILABLE = False
    CyberSecurityAgent = None
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Brigit CyberSecurityAgent not available. Departmental orchestrator will use limited agents.")

# Guard all Brigit agent imports
try:
    from brigit.multi_agents.project_management_agent import ProjectManagementAgent
    from brigit.multi_agents.business_analyst_agent import BusinessAnalystAgent
    from brigit.multi_agents.design_agent import DesignAgent
    from brigit.multi_agents.quality_assurance_agent import QualityAssuranceAgent
    BRIGIT_PROJECT_AGENTS_AVAILABLE = True
except ImportError:
    ProjectManagementAgent = None
    BusinessAnalystAgent = None
    DesignAgent = None
    QualityAssuranceAgent = None
    BRIGIT_PROJECT_AGENTS_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning("Brigit project agents not available. Departmental orchestrator will use basic agents only.")
# Make kev agents optional - they may not be available in all deployments
try:
    from kev.multi_agents.learning_and_development_agent import LearningDevelopmentAgent
    KEV_AGENTS_AVAILABLE = True
except ImportError:
    KEV_AGENTS_AVAILABLE = False
    LearningDevelopmentAgent = None
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Kev LearningDevelopmentAgent not available. Departmental orchestrator will use limited agents.")

try:
    from brigit.multi_agents.event_planning_agent import EventPlanningAgent
    from brigit.multi_agents.graphic_design_agent import GraphicDesignerAgent
    BRIGIT_EVENT_AGENTS_AVAILABLE = True
except ImportError as e:
    EventPlanningAgent = None
    GraphicDesignerAgent = None
    BRIGIT_EVENT_AGENTS_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"Brigit event/design agents not available: {e}.")

try:
    from brigit.multi_agents.video_production_agent import VideoProductionAgent
    from brigit.multi_agents.social_media_manager_agent import SocialMediaManagerAgent
    from brigit.multi_agents.market_researcher_agent import MarketResearcherAgent
    from brigit.multi_agents.publisher_agent import PublisherAgent
    from brigit.multi_agents.copywriter_agent import CopywriterAgent
    BRIGIT_MEDIA_AGENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Brigit media agents not available: {e}. Departmental orchestrator will use basic agents only.")
    VideoProductionAgent = None
    SocialMediaManagerAgent = None
    MarketResearcherAgent = None
    PublisherAgent = None
    CopywriterAgent = None
    BRIGIT_MEDIA_AGENTS_AVAILABLE = False

try:
    from shared_resources.multi_agents.seo_agent import SEOAgent
    SEO_AGENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"SEO agent not available: {e}.")
    SEOAgent = None
    SEO_AGENT_AVAILABLE = False

# Placeholder for future departmental agents
# from brigit.multi_agents.procurement_agent
# from brigit.multi_agents.legal_agent
# from brigit.multi_agents.treasury_ops_agent
# from brigit.multi_agents.customer_support_agent
# from brigit.multi_agents.supply_chain_agent
# from brigit.multi_agents.product_management_agent

from backend.utils.watchdog import Watchdog
from backend.governance.ethical_framework import EthicalScaffoldingManager
from backend.governance.regulatory_compliance import ComplianceEngine
from backend.multi_agent.dynamic_threat_detector import DynamicThreatDetector, ThreatEvent, ThreatType, ThreatLevel

logger = logging.getLogger(__name__)

class DepartmentalOrchestrator:
    """
    Manages departmental agents and cross-cutting concerns like system monitoring,
    ethical frameworks, and regulatory compliance, *within PRIV's application domain*.
    It interacts with the message broker provided by PRIV's Central Orchestrator.
    """
    def __init__(self, message_broker_interface: MessageBrokerInterface, zk_verifier: Any): 
        self.message_broker_interface = message_broker_interface
        self.reputation_ledger = AgentReputationLedger()
        self.arbitration_engine = ArbitrationEngine(self.message_broker_interface, zk_verifier)
        self.message_broker_interface = message_broker_interface
        self.agents: Dict[str, PrivAgent] = {}
        self.is_running = False
        self.agent_message_queue = asyncio.Queue()
        self.processing_task = None

        # Initialize cross-cutting services managed by this orchestrator
        # Note: Watchdog and DynamicThreatDetector are now managed by CentralOrchestrator
        # self.watchdog = Watchdog()
        # self.dynamic_threat_detector = DynamicThreatDetector(self.message_broker_interface)
        self.ethical_scaffolding_manager = EthicalScaffoldingManager()
        self.compliance_engine = ComplianceEngine()

        self._initialize_agents()
        logger.info("Departmental Orchestrator initialized.")

    def _initialize_agents(self):
        """Initializes departmental agents."""
        logger.info("Initializing departmental agents...")

        # Only initialize agents if they were successfully imported
        if BRIGIT_CORE_AGENTS_AVAILABLE:
            if ITAgent is not None:
                self.agents[AgentType.IT.value] = ITAgent(agent_id="it-001", message_broker=self.message_broker_interface, persona={})
            if AccountsAgent is not None:
                self.agents[AgentType.ACCOUNTS.value] = AccountsAgent(agent_id="accounts-001", message_broker=self.message_broker_interface, persona={})
            if DataAnalystAgent is not None:
                self.agents[AgentType.DATA_ANALYST.value] = DataAnalystAgent(agent_id="data-analyst-001", message_broker=self.message_broker_interface, persona={})
            if PatentResearcherAgent is not None:
                self.agents[AgentType.PATENT_RESEARCHER.value] = PatentResearcherAgent(agent_id="patent-researcher-001", message_broker=self.message_broker_interface, persona={})
            if HRAgent is not None:
                self.agents[AgentType.HR.value] = HRAgent(agent_id="hr-001", message_broker=self.message_broker_interface, persona={})
            if MarketingAgent is not None:
                self.agents[AgentType.MARKETING.value] = MarketingAgent(agent_id="marketing-001", message_broker=self.message_broker_interface, persona={})
            if InnovationAgent is not None:
                self.agents[AgentType.INNOVATION.value] = InnovationAgent(agent_id="innovation-001", message_broker=self.message_broker_interface, persona={})
            if SalesAgent is not None:
                self.agents[AgentType.SALES.value] = SalesAgent(agent_id="sales-001", message_broker=self.message_broker_interface, persona={})
            if ContentEditorAgent is not None:
                self.agents[AgentType.CONTENT_EDITOR.value] = ContentEditorAgent(agent_id="content-editor-001", message_broker=self.message_broker_interface, persona={})
            if ArticleWriterAgent is not None:
                self.agents[AgentType.ARTICLE_WRITER.value] = ArticleWriterAgent(agent_id="article-writer-001", message_broker=self.message_broker_interface, persona={})
            if DataScraperAgent is not None:
                self.agents[AgentType.DATA_SCRAPER.value] = DataScraperAgent(agent_id="data-scraper-001", message_broker=self.message_broker_interface, persona={})
        else:
            logger.warning("Brigit core agents not available. Skipping core agent initialization.")

        if BRIGIT_EVENT_AGENTS_AVAILABLE and GraphicDesignerAgent is not None:
            self.agents[AgentType.GRAPHIC_DESIGN.value] = GraphicDesignerAgent(agent_id="graphic-designer-001", message_broker=self.message_broker_interface, persona={})

        if BRIGIT_MEDIA_AGENTS_AVAILABLE and MarketResearcherAgent is not None:
            self.agents[AgentType.MARKET_RESEARCHER.value] = MarketResearcherAgent(agent_id="market-researcher-001", message_broker=self.message_broker_interface, persona={})

        if BRIGIT_MEDIA_AGENTS_AVAILABLE and PublisherAgent is not None:
            self.agents[AgentType.PUBLISHER.value] = PublisherAgent(agent_id="publisher-001", message_broker=self.message_broker_interface, persona={})

        if SEO_AGENT_AVAILABLE and SEOAgent is not None:
            self.agents[AgentType.SEO.value] = SEOAgent(agent_id="seo-001", message_broker=self.message_broker_interface, persona={})
        if BRIGIT_AGENTS_AVAILABLE and CyberSecurityAgent is not None:
            self.agents[AgentType.CYBERSECURITY.value] = CyberSecurityAgent(agent_id="cybersecurity-001", message_broker=self.message_broker_interface, persona={})
        else:
            logger.warning("CyberSecurityAgent not available. Skipping initialization.")
        
        if BRIGIT_PROJECT_AGENTS_AVAILABLE and ProjectManagementAgent is not None:
            self.agents[AgentType.PROJECT_MANAGEMENT.value] = ProjectManagementAgent(agent_id="project-management-001", message_broker=self.message_broker_interface, persona={})
        else:
            logger.warning("ProjectManagementAgent not available. Skipping initialization.")
            
        if BRIGIT_PROJECT_AGENTS_AVAILABLE and BusinessAnalystAgent is not None:
            self.agents[AgentType.BUSINESS_ANALYST.value] = BusinessAnalystAgent(agent_id="business-analyst-001", message_broker=self.message_broker_interface, persona={})
        else:
            logger.warning("BusinessAnalystAgent not available. Skipping initialization.")
            
        if BRIGIT_PROJECT_AGENTS_AVAILABLE and DesignAgent is not None:
            self.agents[AgentType.DESIGN.value] = DesignAgent(agent_id="design-001", message_broker=self.message_broker_interface, persona={})
        else:
            logger.warning("DesignAgent not available. Skipping initialization.")
            
        if BRIGIT_PROJECT_AGENTS_AVAILABLE and QualityAssuranceAgent is not None:
            self.agents[AgentType.QUALITY_ASSURANCE.value] = QualityAssuranceAgent(agent_id="quality-assurance-001", message_broker=self.message_broker_interface, persona={})
        else:
            logger.warning("QualityAssuranceAgent not available. Skipping initialization.")
            
        if KEV_AGENTS_AVAILABLE and LearningDevelopmentAgent is not None:
            self.agents[AgentType.LEARNING_DEVELOPMENT.value] = LearningDevelopmentAgent(agent_id="learning-and-development-001", message_broker=self.message_broker_interface, persona={})
        else:
            logger.warning("LearningDevelopmentAgent not available. Skipping initialization.")

        if BRIGIT_EVENT_AGENTS_AVAILABLE and EventPlanningAgent is not None:
            self.agents[AgentType.EVENT_PLANNING.value] = EventPlanningAgent(agent_id="event-planning-001", message_broker=self.message_broker_interface, persona={})

        if BRIGIT_MEDIA_AGENTS_AVAILABLE and SocialMediaManagerAgent is not None:
            self.agents[AgentType.SOCIAL_MEDIA_MANAGER.value] = SocialMediaManagerAgent(agent_id="social-media-manager-001", message_broker=self.message_broker_interface, persona={})
        else:
            logger.warning("SocialMediaManagerAgent not available. Skipping initialization.")

        if BRIGIT_MEDIA_AGENTS_AVAILABLE and CopywriterAgent is not None:
            self.agents[AgentType.COPYWRITER.value] = CopywriterAgent(agent_id="copywriter-001", message_broker=self.message_broker_interface, persona={})
        else:
            logger.warning("CopywriterAgent not available. Skipping initialization.")

        if BRIGIT_MEDIA_AGENTS_AVAILABLE and VideoProductionAgent is not None:
            self.agents[AgentType.VIDEO_PRODUCTION.value] = VideoProductionAgent(agent_id="video-production-001", message_broker=self.message_broker_interface, persona={})

        # Log summary of initialized agents
        logger.info(f"Departmental agents initialized: {len(self.agents)} agents available")
        # Placeholder for future departmental agents
        # self.agents[AgentType.PROCUREMENT.value] = 
        # self.agents[AgentType.LEGAL.value] = 
        # self.agents[AgentType.TREASURY_OPS.value] = 
        # self.agents[AgentType.CUSTOMER_SUPPORT.value] = 
        # self.agents[AgentType.SUPPLY_CHAIN.value] = 
        # Self.agents[AgentType.PRODUCT_MANAGEMENT.value] = 
        # Add other departmental agents here as they are developed
        # For example: HR Agent, Marketing Agent, etc.

        logger.info(f"Initialized {len(self.agents)} departmental agents.")
        
        self._merge_mpeti_skills_to_departmental_agents()

    def _merge_mpeti_skills_to_departmental_agents(self):
        """
        Merges MPETI's self-healing, governance, and conflict resolution skills
        into each departmental agent.
        """
        logger.info("Merging MPETI's resiliency skills into departmental agents...")

        mpeti_healing_protocols = ["reset_connection", "restart_module"]
        mpeti_governance_rules = self.compliance_engine.get_active_rules_ids() + self.ethical_scaffolding_manager.get_active_principles_ids()
        
        for agent_id, agent_instance in self.agents.items():
            if isinstance(agent_instance, PrivAgent):
                agent_instance.inherited_healing_protocols.extend(mpeti_healing_protocols)
                agent_instance.inherited_governance_rules.extend(mpeti_governance_rules)
                logger.info(f"Departmental Agent {agent_id} inherited MPETI's resiliency skills.")

    async def start(self):
        """Starts the departmental orchestrator and its managed agents."""
        if self.is_running:
            logger.warning("Departmental Orchestrator is already running.")
            return

        self.is_running = True
        # Message broker connection is managed by CentralOrchestrator
        # await self.message_broker_interface.connect() 
        logger.info("Departmental Orchestrator starting message broker connection.")

        for agent_id, agent_instance in self.agents.items():
            await agent_instance.start()
            logger.info(f"Departmental Agent {agent_id} started by Departmental Orchestrator.")

        self.processing_task = asyncio.create_task(self._listen_for_orchestrator_messages())
        # Watchdog and DynamicThreatDetector are now started by CentralOrchestrator
        # self.dynamic_threat_detector.start_monitoring()
        # self.watchdog.start_monitoring()
        logger.info("Departmental Orchestrator fully operational.")

    async def stop(self):
        """Stops the departmental orchestrator and its managed agents."""
        if not self.is_running:
            logger.warning("Departmental Orchestrator is not running.")
            return

        self.is_running = False
        logger.info("Stopping Departmental Orchestrator...")

        for agent_id, agent_instance in self.agents.items():
            await agent_instance.stop()
            logger.info(f"Departmental Agent {agent_id} stopped by Departmental Orchestrator.")

        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                logger.info("Departmental Orchestrator processing task cancelled.")
        
        # Watchdog and DynamicThreatDetector are now stopped by CentralOrchestrator
        # await self.dynamic_threat_detector.stop_monitoring()
        # await self.watchdog.stop_monitoring()
        # Message broker disconnection is managed by CentralOrchestrator
        # await self.message_broker_interface.disconnect()
        logger.info("Departmental Orchestrator disconnected message broker.")
        logger.info("Departmental Orchestrator stopped.")

    async def _listen_for_orchestrator_messages(self):
        """
        Listens for messages relevant to the departmental orchestrator
        (e.g., system status, critical logs, threat events).
        """
        system_status_sub = f"projects/{settings.GCP_PROJECT_ID}/subscriptions/system_status_updates-sub"
        threat_events_sub = f"projects/{settings.GCP_PROJECT_ID}/subscriptions/threat_events-sub"
        critical_logs_sub = f"projects/{settings.GCP_PROJECT_ID}/subscriptions/mpeti-critical-logs-sub"

        async def system_status_callback(message):
            try:
                status_update = json.loads(message.data.decode('utf-8'))
                logger.info(f"Departmental Orchestrator received system status update: {status_update.get('component')} - {status_update.get('status')}")
                if status_update.get("status") == "FAILED":
                    component = status_update.get("component")
                    logger.warning(f"System component {component} failed. Departmental Orchestrator assessing impact.")
                    it_agent = self.agents.get(AgentType.IT.value)
                    if it_agent:
                        await it_agent.handle_message(
                            AgentMessage(
                                sender_id="departmental-orchestrator",
                                sender_type=AgentType.DEPARTMENTAL_ORCHESTRATOR,
                                recipient_id=it_agent.agent_id,
                                message_type="system_failure_alert",
                                content={"component": component, "details": status_update.get("details")}
                            )
                        )
                message.ack()
            except Exception as e:
                logger.error(f"Error handling system status update: {e}", exc_info=True)
                message.nack()

        async def threat_event_callback(message):
            try:
                threat_event = ThreatEvent.parse_raw(message.data)
                logger.warning(f"Departmental Orchestrator received threat event: {threat_event.threat_type.value} - {threat_event.threat_level.value}")
                it_agent = self.agents.get(AgentType.IT.value)
                if it_agent:
                    await it_agent.handle_message(
                        AgentMessage(
                            sender_id="departmental-orchestrator",
                            sender_type=AgentType.DEPARTMENTAL_ORCHESTRATOR,
                            recipient_id=it_agent.agent_id,
                            message_type="security_threat_alert",
                            content={"threat_event": threat_event.dict()}
                        )
                    )
                message.ack()
            except Exception as e:
                logger.error(f"Error handling threat event: {e}", exc_info=True)
                message.nack()
        
        async def critical_logs_callback(message):
            try:
                log_entry = json.loads(message.data.decode('utf-8'))
                logger.error(f"Departmental Orchestrator received critical log: {log_entry.get('component')} - {log_entry.get('details')}")
                message.ack()
            except Exception as e:
                logger.error(f"Error handling critical log: {e}", exc_info=True)
                message.nack()

        self.message_broker_interface.subscribe(system_status_sub, system_status_callback)
        self.message_broker_interface.subscribe(threat_events_sub, threat_event_callback)
        self.message_broker_interface.subscribe(critical_logs_sub, critical_logs_callback)

        while self.is_running:
            await asyncio.sleep(1)

