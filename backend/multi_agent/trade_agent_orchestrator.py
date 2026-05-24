# priv/backend/multi_agent/trade_agent_orchestrator.py
import asyncio
import logging
from typing import Dict, Any, List
from collections import deque
import json

from backend.multi_agent.priv_agent_protocol import AgentType, AgentMessage, TradeProposal, ArbitrationVote, ArbitrationDecision
from backend.multi_agent.message_broker_interface import MessageBrokerInterface, GoogleCloudPubSubBroker
from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.agent_reputation_ledger import AgentReputationLedger
from backend.multi_agent.arbitration_engine import ArbitrationEngine
from backend.multi_agent.vote_history_ledger import VoteHistoryLedger
from datetime import datetime
from backend.config import settings

# Import only trade-specific Priv agents and their direct dependencies
from backend.multi_agent.priv_compliance_agent import PrivComplianceAgent
from backend.multi_agent.priv_arbitrage_agent import PrivArbitrageAgent
from backend.multi_agent.priv_economic_agent import PrivEconomicAgent
from backend.multi_agent.priv_execution_agent import PrivExecutionAgent
from backend.multi_agent.priv_political_agent import PrivPoliticalAgent
from backend.multi_agent.priv_portfolio_manager_agent import PrivPortfolioManagerAgent
from backend.multi_agent.priv_quantitative_agent import PrivQuantitativeAgent
from backend.multi_agent.priv_risk_agent import PrivRiskAgent
from backend.multi_agent.priv_sentiment_agent import PrivSentimentAgent
from backend.multi_agent.priv_strategist_agent import PrivStrategistAgent
from backend.multi_agent.priv_technical_agent import PrivTechnicalAgent
from backend.multi_agent.priv_commodity_agent import PrivCommodityAgent
from backend.multi_agent.priv_futures_agent import PrivFuturesAgent
from backend.multi_agent.priv_credit_agent import PrivCreditAgent
from backend.multi_agent.priv_legal_agent import PrivLegalAgent # For trade-related legal compliance
from backend.multi_agent.priv_audit_agent import PrivAuditAgent # For trade auditing
from backend.multi_agent.priv_ai_ops_agent import PrivAIOpsAgent # For operational health of trade systems
from backend.multi_agent.priv_research_agent import PrivResearchAgent # Provides research for trade decisions
from backend.multi_agent.priv_fomc_agent import PrivFOMCAgent
from backend.multi_agent.priv_yield_optimizer_agent import PrivYieldOptimizerAgent
from backend.multi_agent.priv_alternative_data_agent import PrivAlternativeDataAgent # Provides data for trade decisions
from backend.multi_agent.priv_news_analysis_agent import PrivNewsAnalysisAgent # Provides data for trade decisions
from backend.multi_agent.priv_social_media_agent import PrivSocialMediaAgent # Provides data for trade decisions
from backend.multi_agent.priv_tax_agent import PrivTaxAgent # Has trade implications
from backend.multi_agent.priv_ml_agent import PrivMLAgent # Directly involved in trade model management
from backend.multi_agent.priv_options_agent import PrivOptionsAgent
from backend.multi_agent.priv_forex_agent import PrivForexAgent
from backend.multi_agent.priv_synthetic_markets_agent import PrivSyntheticMarketsAgent
from backend.multi_agent.priv_sensory_agent import PrivSensoryAgent # Provides data for trade context
from backend.multi_agent.priv_regulatory_arbiter_agent import PrivRegulatoryArbiterAgent
from backend.multi_agent.priv_ethical_arbiter_agent import PrivEthicalArbiterAgent
from backend.governance.tokenization.zk_verifier import ZKVerifier

# Note: Departmental agents and cross-cutting services like Watchdog, DynamicThreatDetector
# are now managed by CentralOrchestrator or DepartmentalOrchestrator.

logger = logging.getLogger(__name__)

class TradeAgentOrchestrator:
    """
    Specialized orchestrator for Priv's trade-related agents.
    Manages agent lifecycles, message routing, and arbitration for trade proposals.
    """
    # UPDATED the __init__ method signature
    def __init__(self, message_broker_interface: MessageBrokerInterface, zk_verifier: ZKVerifier):
        self.message_broker_interface = message_broker_interface
        self.zk_verifier = zk_verifier  
        self.reputation_ledger = AgentReputationLedger()
        self.vote_ledger = VoteHistoryLedger()
        
        # UPDATED to pass reputation ledger and zk_verifier to ArbitrationEngine
        self.arbitration_engine = ArbitrationEngine(self.reputation_ledger, self.zk_verifier)
        
        self.agents: Dict[str, PrivAgent] = {}
        self.is_running = False
        self.agent_message_queue = asyncio.Queue()
        self.processing_task = None

        self._initialize_agents()
        logger.info("Trade Agent Orchestrator initialized.")

    def _initialize_agents(self):
        """Initializes all specialized Priv agents focused on trade."""
        logger.info("Initializing specialized Priv trade agents...")
        self.agents[AgentType.NEWS_ANALYSIS.value] = PrivNewsAnalysisAgent(
            agent_id="news-analysis-001",
            agent_type=AgentType.NEWS_ANALYSIS,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "news_analyst", "style": "objective"}
            )
        self.agents[AgentType.COMPLIANCE.value] = PrivComplianceAgent(
            agent_id="compliance-001",
            agent_type=AgentType.COMPLIANCE,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "compliance_officer", "style": "meticulous"}
        )
        self.agents[AgentType.ARBITRAGE.value] = PrivArbitrageAgent(
            agent_id="arbitrage-001",
            agent_type=AgentType.ARBITRAGE,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "arbitrage_specialist", "style": "analytical"}
        )
        self.agents[AgentType.ECONOMIC.value] = PrivEconomicAgent(
            agent_id="economic-001",
            agent_type=AgentType.ECONOMIC,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "economic_analyst", "style": "insightful"}
        )
        self.agents[AgentType.EXECUTION.value] = PrivExecutionAgent(
            agent_id="execution-001",
            agent_type=AgentType.EXECUTION,
            message_broker=self.message_broker_interface,
            broker=settings.TRADING_BROKER_ROUTER,
            persona={"role": "trade_executor", "style": "precise"}
        )
        self.agents[AgentType.POLITICAL.value] = PrivPoliticalAgent(
            agent_id="political-001",
            agent_type=AgentType.POLITICAL,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "political_analyst", "style": "contextual"}
        )
        self.agents[AgentType.PORTFOLIO_MANAGER.value] = PrivPortfolioManagerAgent(
            agent_id="portfolio-manager-001",
            agent_type=AgentType.PORTFOLIO_MANAGER,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "portfolio_manager", "style": "strategic"}
        )
        self.agents[AgentType.QUANTITATIVE.value] = PrivQuantitativeAgent(
            agent_id="quantitative-001",
            agent_type=AgentType.QUANTITATIVE,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "quantitative_analyst", "style": "data-driven"}
        )
        self.agents[AgentType.RISK.value] = PrivRiskAgent(
            agent_id="risk-001",
            agent_type=AgentType.RISK,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "risk_manager", "style": "cautious"}
        )
        self.agents[AgentType.SENTIMENT.value] = PrivSentimentAgent(
            agent_id="sentiment-001",
            agent_type=AgentType.SENTIMENT,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "sentiment_analyst", "style": "observant"}
        )
        self.agents[AgentType.STRATEGIST.value] = PrivStrategistAgent(
            agent_id="strategist-001",
            agent_type=AgentType.STRATEGIST,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "trading_strategist", "style": "visionary"}
        )
        self.agents[AgentType.TECHNICAL.value] = PrivTechnicalAgent(
            agent_id="technical-001",
            agent_type=AgentType.TECHNICAL,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "technical_analyst", "style": "detail-oriented"}
        )
        self.agents[AgentType.COMMODITY.value] = PrivCommodityAgent(
            agent_id="commodity-001",
            agent_type=AgentType.COMMODITY,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "commodity_specialist", "style": "market-savvy"}
        )
        self.agents[AgentType.FUTURES.value] = PrivFuturesAgent(
            agent_id="futures-001",
            agent_type=AgentType.FUTURES,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "futures_trader", "style": "forward-thinking"}
        )
        self.agents[AgentType.CREDIT.value] = PrivCreditAgent(
            agent_id="credit-001",
            agent_type=AgentType.CREDIT,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "credit_analyst", "style": "thorough"}
        )
        self.agents[AgentType.LEGAL.value] = PrivLegalAgent(
            agent_id="legal-001",
            agent_type=AgentType.LEGAL,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "legal_advisor", "style": "precise"}
        )
        self.agents[AgentType.AUDIT.value] = PrivAuditAgent(
            agent_id="audit-001",
            agent_type=AgentType.AUDIT,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "auditor", "style": "diligent"}
        )
        self.agents[AgentType.AI_OPS.value] = PrivAIOpsAgent(
            agent_id="ai-ops-001",
            agent_type=AgentType.AI_OPS,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "ai_operations_specialist", "style": "proactive"}
        )
        self.agents[AgentType.RESEARCH.value] = PrivResearchAgent(
            agent_id="research-001",
            agent_type=AgentType.RESEARCH,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "research_analyst", "style": "inquisitive"}
        )
        self.agents[AgentType.FOMC.value] = PrivFOMCAgent(
            agent_id="fomc-001",
            agent_type=AgentType.FOMC,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "fomc_specialist", "style": "insightful"}
        )
        self.agents[AgentType.YIELD_OPTIMIZER.value] = PrivYieldOptimizerAgent(
            agent_id="yield-optimizer-001",
            agent_type=AgentType.YIELD_OPTIMIZER,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "yield_optimizer", "style": "strategic"}
        )
        self.agents[AgentType.ALTERNATIVE_DATA.value] = PrivAlternativeDataAgent(
            agent_id="alt-data-001",
            agent_type=AgentType.ALTERNATIVE_DATA,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "data_analyst", "style": "curious"}
        )
        self.agents[AgentType.SOCIAL_MEDIA.value] = PrivSocialMediaAgent(
            agent_id="social-media-001",
            agent_type=AgentType.SOCIAL_MEDIA,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "social_media_analyst", "style": "attentive"}
        )
        self.agents[AgentType.TAX.value] = PrivTaxAgent(
            agent_id="tax-001",
            agent_type=AgentType.TAX,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "tax_specialist", "style": "accurate"}
        )
        self.agents[AgentType.ML.value] = PrivMLAgent(
            agent_id="ml-001",
            agent_type=AgentType.ML,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "ml_engineer", "style": "innovative"}
        )
        self.agents[AgentType.OPTIONS.value] = PrivOptionsAgent(
            agent_id="options-001",
            agent_type=AgentType.OPTIONS,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "options_trader", "style": "strategic"}
        )
        self.agents[AgentType.FOREX.value] = PrivForexAgent(
            agent_id="forex-001",
            agent_type=AgentType.FOREX,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "forex_trader", "style": "analytical"}
        )
        self.agents[AgentType.SYNTHETIC_MARKETS.value] = PrivSyntheticMarketsAgent(
            agent_id="synthetic-markets-001",
            agent_type=AgentType.SYNTHETIC_MARKETS,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "synthetic_markets_specialist", "style": "innovative"}
        )
        self.agents[AgentType.SENSORY.value] = PrivSensoryAgent(
            agent_id="sensory-001",
            agent_type=AgentType.SENSORY,
            message_broker=self.message_broker_interface,
            broker=self.message_broker_interface,
            persona={"role": "sensory_data_analyst", "style": "observant"}
        )
        self.agents[AgentType.REGULATORY_ARBITER.value] = PrivRegulatoryArbiterAgent(
            agent_id="reg-arbiter-001",
            agent_type=AgentType.REGULATORY_ARBITER,
            message_broker=self.message_broker_interface,
            zk_verifier=self.zk_verifier,  # <-- PASS the zk_verifier
            broker=self.message_broker_interface,
            persona={"role": "regulatory_arbiter", "style": "impartial"}
        )
        self.agents[AgentType.ETHICAL_ARBITER.value] = PrivEthicalArbiterAgent(
            agent_id="eth-arbiter-001",
            agent_type=AgentType.ETHICAL_ARBITER,
            message_broker=self.message_broker_interface,
            zk_verifier=self.zk_verifier,  # <-- PASS the zk_verifier
            broker=self.message_broker_interface,
            persona={"role": "ethical_arbiter", "style": "principled"}
        )
        logger.info(f"Initialized {len(self.agents)} Priv trade agents.")
        
        # Trade agents might also inherit some MPETI skills (if needed)
        # This would be handled by the Central Orchestrator if it's the source of truth for these.
        # For now, we assume the Central Orchestrator will manage this skill merging.

    async def start(self):
        """Starts the trade agent orchestrator and all managed agents."""
        if self.is_running:
            logger.warning("Trade Agent Orchestrator is already running.")
            return

        self.is_running = True
        # Message broker connection is handled by CentralOrchestrator
        # await self.message_broker_interface.connect() 
        logger.info("Trade Agent Orchestrator starting agents.")

        # Start each agent and track status
        started_agents = []
        failed_agents = []
        
        for agent_id, agent_instance in self.agents.items():
            try:
                await agent_instance.start()
                started_agents.append(agent_id)
                logger.info(f"✓ Trade Agent '{agent_id}' started successfully.")
            except Exception as e:
                failed_agents.append((agent_id, str(e)))
                logger.error(f"✗ Trade Agent '{agent_id}' failed to start: {e}", exc_info=True)

        # Log comprehensive registry snapshot
        logger.info("\n" + "="*80)
        logger.info("TRADE ORCHESTRATOR AGENT REGISTRY SNAPSHOT")
        logger.info("="*80)
        logger.info(f"Total Agents: {len(self.agents)}")
        logger.info(f"Successfully Started: {len(started_agents)}/{len(self.agents)}")
        logger.info(f"Failed to Start: {len(failed_agents)}/{len(self.agents)}")
        
        if failed_agents:
            logger.warning("\nFailed Agents:")
            for agent_id, error in failed_agents:
                logger.warning(f"  - {agent_id}: {error}")
        
        logger.info("\nActive Agents by Type:")
        agents_by_type = {}
        for agent_id in started_agents:
            agent_type = agent_id.split('-')[0].upper()
            if agent_type not in agents_by_type:
                agents_by_type[agent_type] = []
            agents_by_type[agent_type].append(agent_id)
        
        for agent_type in sorted(agents_by_type.keys()):
            count = len(agents_by_type[agent_type])
            logger.info(f"  {agent_type}: {count}")
        
        logger.info("="*80 + "\n")

        # Trade Orchestrator listens for trade-specific messages
        self.processing_task = asyncio.create_task(self._listen_for_trade_messages())
        logger.info("Trade Agent Orchestrator fully operational.")

    async def stop(self):
        """Stops the trade agent orchestrator and all managed agents."""
        if not self.is_running:
            logger.warning("Trade Agent Orchestrator is not running.")
            return

        self.is_running = False
        logger.info("Stopping Trade Agent Orchestrator...")

        for agent_id, agent_instance in self.agents.items():
            await agent_instance.stop()
            logger.info(f"Trade Agent {agent_id} stopped by Orchestrator.")

        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                logger.info("Trade Agent Orchestrator processing task cancelled.")

        # Message broker disconnection is handled by CentralOrchestrator
        # await self.message_broker_interface.disconnect()
        logger.info("Trade Agent Orchestrator stopped.")

    async def _listen_for_trade_messages(self):
        """
        Listens for messages relevant to trade agents (e.g., new proposals, votes, decisions).
        """
        proposal_sub = f"projects/{settings.GCP_PROJECT_ID}/subscriptions/trade_proposals-sub"
        vote_sub = f"projects/{settings.GCP_PROJECT_ID}/subscriptions/arbitration_votes-sub"
        decision_sub = f"projects/{settings.GCP_PROJECT_ID}/subscriptions/arbitration_decisions-sub"

        async def proposal_callback(message):
            try:
                proposal = TradeProposal.parse_raw(message.data)
                logger.info(f"Trade Orchestrator received proposal: {proposal.proposal_id}")
                await self.arbitration_engine.handle_proposal(proposal)
                message.ack()
            except Exception as e:
                logger.error(f"Error handling proposal: {e}", exc_info=True)
                message.nack()

        async def vote_callback(message):
            try:
                vote = ArbitrationVote.parse_raw(message.data)
                # Ensure we have a vote_id -- generate one if missing
                vote_id = getattr(vote, 'vote_id', None) or f"{vote.proposal_id}-{vote.voting_agent_id}-{int(datetime.utcnow().timestamp())}"
                logger.info(f"Trade Orchestrator received vote: {vote_id} for {vote.proposal_id} by {vote.voting_agent_id}")
                # Record to the local vote ledger
                try:
                    self.vote_ledger.record_vote(agent_id=vote.voting_agent_id, proposal_id=vote.proposal_id, vote=vote.vote, reasoning=vote.reasoning, confidence=vote.confidence, vote_id=vote_id)
                except Exception as e:
                    logger.warning(f"Failed to persist vote to ledger: {e}")
                # Forward to arbitration engine if implemented
                if hasattr(self.arbitration_engine, 'handle_vote'):
                    await self.arbitration_engine.handle_vote(vote)
                message.ack()
            except Exception as e:
                logger.error(f"Error handling vote: {e}", exc_info=True)
                message.nack()

        async def decision_callback(message):
            try:
                decision = ArbitrationDecision.parse_raw(message.data)
                logger.info(f"Trade Orchestrator received decision: {decision.decision_id} for {decision.proposal_id}")
                await self._distribute_decision(decision)
                message.ack()
            except Exception as e:
                logger.error(f"Error handling decision: {e}", exc_info=True)
                message.nack()

        self.message_broker_interface.subscribe(proposal_sub, proposal_callback)
        self.message_broker_interface.subscribe(vote_sub, vote_callback)
        self.message_broker_interface.subscribe(decision_sub, decision_callback)

        while self.is_running:
            await asyncio.sleep(1)

    async def _distribute_decision(self, decision: ArbitrationDecision):
        """Distributes the final arbitration decision to relevant agents."""
        logger.info(f"Distributing arbitration decision {decision.decision_id} (status: {decision.status.value}).")
        if decision.status == ArbitrationDecision.DecisionStatus.APPROVED:
            execution_agent = self.agents.get(AgentType.EXECUTION.value)
            if execution_agent:
                await execution_agent.handle_message(
                    AgentMessage(
                        sender_id="trade-orchestrator",
                        sender_type=AgentType.ORCHESTRATOR, # Still use Orchestrator type for protocol consistency
                        recipient_id=execution_agent.agent_id,
                        message_type="execute_trade",
                        content={"proposal_id": decision.proposal_id, "trade_details": decision.trade_details}
                    )
                )
        for agent in self.agents.values():
            if agent.agent_id != AgentType.EXECUTION.value:
                await agent.handle_message(
                    AgentMessage(
                        sender_id="trade-orchestrator",
                        sender_type=AgentType.ORCHESTRATOR,
                        recipient_id=agent.agent_id,
                        message_type="arbitration_result",
                        content={"decision": decision.dict()}
                    )
                )
        
        if decision.status == ArbitrationDecision.DecisionStatus.APPROVED and \
           decision.resolution_type == ArbitrationDecision.ResolutionType.SYSTEM_HEALING:
            affected_agent_id = decision.trade_details.get("affected_agent_id")
            healing_protocol = decision.trade_details.get("healing_protocol")
            if affected_agent_id and healing_protocol:
                affected_agent = self.agents.get(affected_agent_id)
                if affected_agent:
                    await affected_agent.apply_healing_protocol(healing_protocol, decision.trade_details.get("healing_params", {}))
        
        for agent in self.agents.values():
            feedback = {
                "proposal_id": decision.proposal_id,
                "decision_status": decision.status.value,
                "performance": 1.0 if decision.status == ArbitrationDecision.DecisionStatus.APPROVED else 0.0,
                "reason": decision.reason
            }
            await agent.receive_feedback(feedback)

