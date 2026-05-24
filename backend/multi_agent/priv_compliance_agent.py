import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from backend.multi_agent.priv_agent import PrivAgent
from backend.multi_agent.priv_agent_protocol import AgentMessage, MessageType, TradeProposal, ArbitrationVote, TradeAction, AgentType
from backend.governance.ethical_framework import EthicalStatus, EthicalSeverity 
from backend.governance.regulatory_compliance import ComplianceStatus
from backend.multi_agent.message_broker_interface import MessageBrokerInterface
from backend.trading_engine.broker_interface import BrokerInterface

logger = logging.getLogger(__name__)

class PrivComplianceAgent(PrivAgent):
    """
    A specialized Priv Agent focused on regulatory and ethical compliance.
    This agent subscribes to trade proposals and generates arbitration votes
    based on compliance rules and ethical guidelines.
    """
    def __init__(self, agent_id: str, agent_type: AgentType, message_broker: MessageBrokerInterface, broker: Optional[BrokerInterface], persona: Dict[str, Any]):
        super().__init__(agent_id=agent_id, agent_type=AgentType.COMPLIANCE, message_broker=message_broker, broker=broker, persona=persona)
        self.message_broker = message_broker
        self.is_running = False
        self.forbidden_symbols: set = {"SANCTIONED_ENTITY_STOCK", "ILLEGAL_CRYPTO"} # Conceptual forbidden list
        self.max_daily_trade_volume_usd = 100000.0 # Conceptual limit
        logger.info(f"Priv Compliance Agent '{self.agent_id}' initialized.")

    async def start(self):
        """Starts the compliance agent, subscribing to trade proposals."""
        if self.is_running:
            logger.warning(f"Compliance Agent '{self.agent_id}' is already running.")
            return

        # Subscribe to trade proposals to evaluate them for compliance
        await self.broker.subscribe_to_topic(
            "trade_proposals", 
            self._handle_trade_proposal_for_compliance_check,
            f"{self.agent_id}-trade-proposals-sub"
        )
        self.is_running = True
        logger.info(f"Compliance Agent '{self.agent_id}' started and subscribed to 'trade_proposals'.")

    async def stop(self):
        """Stops the compliance agent."""
        if not self.is_running:
            logger.warning(f"Compliance Agent '{self.agent_id}' is not running.")
            return
        
        self.is_running = False
        logger.info(f"Compliance Agent '{self.agent_id}' stopped.")

    async def _handle_trade_proposal_for_compliance_check(self, message: Dict[str, Any]):
        """Handle trade proposal messages for compliance checking"""
        try:
            logger.info(f"Compliance Agent '{self.agent_id}' received trade proposal for review")
            
            # Extract trade proposal from message
            if isinstance(message, dict) and "trade_proposal" in message:
                trade_proposal = message["trade_proposal"]
            else:
                trade_proposal = message
            
            # Perform compliance check
            violations = await self.check_trade_compliance(trade_proposal)
            
            # Generate arbitration vote based on violations
            if violations:
                # Cast negative vote if violations found
                logger.warning(f"Compliance Agent '{self.agent_id}' found {len(violations)} violations")
                await self._cast_negative_vote(trade_proposal, violations)
            else:
                # Cast positive vote if compliant
                logger.info(f"Compliance Agent '{self.agent_id}' approved trade proposal")
                await self._cast_positive_vote(trade_proposal)
                
        except Exception as e:
            logger.error(f"Error handling trade proposal in Compliance Agent '{self.agent_id}': {e}", exc_info=True)

    async def _cast_positive_vote(self, trade_proposal: Dict[str, Any]):
        """Cast a positive arbitration vote"""
        vote_message = {
            "agent_id": self.agent_id,
            "proposal_id": trade_proposal.get("proposal_id", "unknown"),
            "vote": "approve",
            "reason": "Trade complies with all regulatory and ethical requirements",
            "timestamp": datetime.now().isoformat()
        }
        await self.message_broker.publish_to_topic("arbitration_votes", vote_message)

    async def _cast_negative_vote(self, trade_proposal: Dict[str, Any], violations: List[Dict[str, Any]]):
        """Cast a negative arbitration vote"""
        vote_message = {
            "agent_id": self.agent_id,
            "proposal_id": trade_proposal.get("proposal_id", "unknown"),
            "vote": "reject",
            "reason": f"Trade has {len(violations)} compliance violations",
            "violations": violations,
            "timestamp": datetime.now().isoformat()
        }
        await self.message_broker.publish_to_topic("arbitration_votes", vote_message)

    async def continuous_compliance_monitoring(self):
        """Continuous compliance monitoring loop"""
        while self.is_running:
            try:
                # Monitor all active trades
                await self.monitor_active_trades()
                
                # Check for regulatory changes
                await self.check_regulatory_updates()
                
                # Monitor market conditions
                await self.monitor_market_conditions()
                
                # Check ethical compliance
                await self.check_ethical_compliance()
                
                # Update compliance dashboard
                await self.update_compliance_dashboard()
                
            except Exception as e:
                logger.error(f"Error in compliance monitoring: {e}")
                await self.handle_monitoring_error(e)
            
            await asyncio.sleep(self.monitoring_interval)
    
    async def monitor_active_trades(self):
        """Monitor all active trades for compliance violations"""
        try:
            # Get active trades from portfolio manager
            active_trades = await self.get_active_trades()
            
            for trade in active_trades:
                violations = await self.check_trade_compliance(trade)
                
                if violations:
                    await self.handle_compliance_violations(violations, trade)
                
        except Exception as e:
            logger.error(f"Error monitoring active trades: {e}")
    
    async def check_trade_compliance(self, trade: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check individual trade for compliance violations"""
        violations = []
        
        try:
            # Extract trade details
            symbol = trade.get("symbol")
            quantity = Decimal(str(trade.get("quantity", 0)))
            price = Decimal(str(trade.get("price", 0)))
            trade_type = trade.get("type", "buy")
            jurisdiction = trade.get("jurisdiction", "US")
            
            # Check symbol restrictions
            symbol_violations = await self.check_symbol_restrictions(symbol)
            violations.extend(symbol_violations)
            
            # Check jurisdiction compliance
            jurisdiction_violations = await self.check_jurisdiction_compliance(trade, jurisdiction)
            violations.extend(jurisdiction_violations)
            
            # Check sanctions compliance
            sanctions_violations = await self.check_sanctions_compliance(symbol, jurisdiction)
            violations.extend(sanctions_violations)
            
            # Check market manipulation
            manipulation_violations = await self.check_market_manipulation(trade)
            violations.extend(manipulation_violations)
            
            # Check insider trading
            insider_violations = await self.check_insider_trading(trade)
            violations.extend(insider_violations)
            
            # Check ethical compliance
            ethical_violations = await self.check_ethical_violations(trade)
            violations.extend(ethical_violations)
            
            # Check security concerns
            security_violations = await self.check_security_concerns(trade)
            violations.extend(security_violations)
            
        except Exception as e:
            logger.error(f"Error checking trade compliance: {e}")
            violations.append({
                "type": ViolationType.REGULATORY_BREACH,
                "severity": "high",
                "description": f"Compliance check error: {str(e)}",
                "trade_id": trade.get("trade_id", "unknown")
            })
        
        return violations
    
    async def check_symbol_restrictions(self, symbol: str) -> List[Dict[str, Any]]:
        """Check if symbol is restricted"""
        violations = []
        
        if symbol in self.restricted_symbols:
            violations.append({
                "type": ViolationType.REGULATORY_BREACH,
                "severity": "critical",
                "description": f"Symbol {symbol} is restricted",
                "symbol": symbol,
                "restriction_type": "regulatory_restriction"
            })
        
        return violations
    
    async def check_jurisdiction_compliance(self, trade: Dict[str, Any], jurisdiction: str) -> List[Dict[str, Any]]:
        """Check compliance with jurisdiction-specific rules"""
        violations = []
        
        try:
            rules = self.compliance_rules.get(jurisdiction, {})
            
            # Check pattern day trader rule (US)
            if jurisdiction == "US" and rules.get("pattern_day_trader_rule"):
                pdt_violations = await self.check_pattern_day_trader_rule(trade)
                violations.extend(pdt_violations)
            
            # Check free-riding prohibition (US)
            if jurisdiction == "US" and rules.get("free_riding_prohibition"):
                free_riding_violations = await self.check_free_riding_rule(trade)
                violations.extend(free_riding_violations)
            
            # Check margin requirements
            if rules.get("margin_requirements"):
                margin_violations = await self.check_margin_requirements(trade, rules["margin_requirements"])
                violations.extend(margin_violations)
            
            # Check short sale restrictions
            if rules.get("short_sale_restrictions") and trade.get("type") == "sell_short":
                short_violations = await self.check_short_sale_restrictions(trade)
                violations.extend(short_violations)
            
            # Check MiFID II compliance (EU/UK)
            if rules.get("mifid_ii_compliance"):
                mifid_violations = await self.check_mifid_ii_compliance(trade)
                violations.extend(mifid_violations)
            
        except Exception as e:
            logger.error(f"Error checking jurisdiction compliance: {e}")
            violations.append({
                "type": ViolationType.REGULATORY_BREACH,
                "severity": "high",
                "description": f"Jurisdiction compliance error: {str(e)}",
                "jurisdiction": jurisdiction
            })
        
        return violations
    
    async def check_pattern_day_trader_rule(self, trade: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check Pattern Day Trader rule compliance"""
        violations = []
        
        # Implementation would check account equity and day trading activity
        # For now, return mock check
        account_equity = await self.get_account_equity()
        
        if account_equity < 25000:
            violations.append({
                'type': 'PATTERN_DAY_TRADER',
                'severity': 'HIGH',
                'message': 'Account equity below PDT minimum'
            })
        
        return violations
    
    async def _handle_trade_proposal(self, message_payload: dict):
        """
        Callback to process incoming trade proposals and generate an arbitration vote.
        """
        try:
            agent_message = AgentMessage.model_validate(message_payload)
            proposal = TradeProposal.model_validate(agent_message.payload)

            logger.info(f"Compliance Agent '{self.agent_id}' received proposal from {proposal.agent_id}: {proposal.action} {proposal.symbol} (Confidence: {proposal.confidence:.2f})")

            # Generate a vote based on compliance assessment
            vote = await self.generate_arbitration_vote(proposal)
            
            # Publish the vote back to the arbitration engine
            vote_message = AgentMessage(
                sender_id=self.agent_id,
                receiver_id="ArbitrationEngine", # Explicitly target ArbitrationEngine
                message_type=MessageType.ARBITRATION_VOTE,
                payload=vote.model_dump()
            )
            await self.broker.publish_message("arbitration_votes", vote_message.model_dump()) # Publish to 'arbitration_votes' topic
            logger.info(f"Compliance Agent '{self.agent_id}' published vote ({vote.vote}) for proposal {proposal.symbol} from {proposal.agent_id}.")

        except Exception as e:
            logger.error(f"Compliance Agent '{self.agent_id}': Error processing trade proposal: {e}", exc_info=True)

    async def generate_arbitration_vote(self, proposal: TradeProposal) -> ArbitrationVote:
        """
        Generates an arbitration vote based on compliance and ethical checks.
        """
        vote = True # Default to approval
        reason = "Proposal appears compliant and ethical."
        weight = 1.0 # Default weight

        # --- Conceptual Compliance & Ethical Logic ---
        # In a real system, this would involve:
        # 1. Calling a PolicyCompiler/RegulatoryCompliance module.
        # 2. Checking against a live list of sanctioned entities/instruments.
        # 3. Performing ethical checks based on the EthicalScaffoldingManager.
        # 4. Analyzing trade volume against daily/account limits.

        # Example: Check for forbidden symbols
        if proposal.symbol.upper() in self.forbidden_symbols:
            vote = False
            reason = f"Proposal involves a forbidden symbol: {proposal.symbol}."
            weight = 1.0 # Highest weight for compliance violation
            logger.critical(f"Compliance Agent '{self.agent_id}': {reason}")
            # In a real system, this would trigger an alert and potentially reputation penalty.

        # Example: Check conceptual daily trade volume limit (very simplified)
        # Assuming proposal.volume is in base currency, and price is current market price
        # This would be tracked across all trades in a real system.
        conceptual_trade_value = proposal.volume * proposal.entry_price if proposal.entry_price else proposal.volume
        if conceptual_trade_value > self.max_daily_trade_volume_usd:
            vote = False
            reason = f"Proposed trade value (${conceptual_trade_value:.2f}) exceeds daily limit (${self.max_daily_trade_volume_usd:.2f})."
            weight = 0.9 # High weight for volume limit violation
            logger.warning(f"Compliance Agent '{self.agent_id}': {reason}")

        # Example: Ethical check (conceptual) - check proposal's risk_assessment for ethical flags
        if proposal.risk_assessment and proposal.risk_assessment.get("ethical_check", {}).get("status") == "NON_COMPLIANT":
            vote = False
            reason = "Proposal flagged as ethically non-compliant."
            weight = 0.95 # Very high weight for ethical violation
            logger.critical(f"Compliance Agent '{self.agent_id}': {reason}")

        return ArbitrationVote(
            proposal_id=f"{proposal.agent_id}-{proposal.symbol}-{datetime.now().timestamp()}", # Unique ID for the proposal
            voter_id=self.agent_id,
            vote=vote,
            weight=weight,
            reason=reason
        )

# Example Usage (for testing PrivComplianceAgent in isolation)
async def main_compliance_agent_test():
    logging.basicConfig(level=logging.INFO)
    from backend.multi_agent.message_broker_interface import GoogleCloudPubSubBroker
    from backend.config import settings

    project_id = settings.GCP_PROJECT_ID
    if not project_id:
        logger.error("GCP_PROJECT_ID not set. Cannot run Pub/Sub test.")
        return

    broker = GoogleCloudPubSubBroker(broker_config={"project_id": project_id})
    compliance_agent = PrivComplianceAgent(
        agent_id="Priv-Compliance",
        broker=broker,
        persona={"name": "Compliance Auditor", "focus": "Regulatory Adherence", "role": "compliance_auditor"}
    )

    await broker.connect()
    await compliance_agent.start()

    # Simulate incoming trade proposals for compliance checks
    mock_proposal_compliant = TradeProposal(
        agent_id="Priv-Strategist", symbol="AAPL", action=TradeAction.BUY, volume=10.0, confidence=0.9,
        reasoning="Strong earnings.", risk_assessment={"ethical_check": {"status": "COMPLIANT"}}
    )
    mock_proposal_forbidden_symbol = TradeProposal(
        agent_id="Priv-Technical", symbol="SANCTIONED_ENTITY_STOCK", action=TradeAction.SELL, volume=1.0, confidence=0.7,
        reasoning="Technical sell signal.", risk_assessment={}
    )
    mock_proposal_high_volume = TradeProposal(
        agent_id="Priv-Economic", symbol="EURUSD", action=TradeAction.BUY, volume=50000.0, entry_price=1.0, confidence=0.8,
        reasoning="Economic forecast.", risk_assessment={}
    )
    mock_proposal_ethical_violation = TradeProposal(
        agent_id="Priv-Strategist", symbol="ETHICALLY_QUESTIONABLE_STOCK", action=TradeAction.BUY, volume=5.0, confidence=0.6,
        reasoning="High potential return.", risk_assessment={"ethical_check": {"status": "NON_COMPLIANT"}}
    )

    logger.info("\n--- Simulating trade proposals for Compliance Agent to evaluate ---")
    await broker.publish_message("trade_proposals", AgentMessage(sender_id="Priv-Strategist", message_type=MessageType.TRADE_PROPOSAL, payload=mock_proposal_compliant.model_dump()).model_dump())
    await asyncio.sleep(1)
    await broker.publish_message("trade_proposals", AgentMessage(sender_id="Priv-Technical", message_type=MessageType.TRADE_PROPOSAL, payload=mock_proposal_forbidden_symbol.model_dump()).model_dump())
    await asyncio.sleep(1)
    await broker.publish_message("trade_proposals", AgentMessage(sender_id="Priv-Economic", message_type=MessageType.TRADE_PROPOSAL, payload=mock_proposal_high_volume.model_dump()).model_dump())
    await asyncio.sleep(1)
    await broker.publish_message("trade_proposals", AgentMessage(sender_id="Priv-Strategist", message_type=MessageType.TRADE_PROPOSAL, payload=mock_proposal_ethical_violation.model_dump()).model_dump())
    await asyncio.sleep(3) # Give time for compliance agent to process and vote

    await compliance_agent.stop()
    await broker.disconnect()
    logger.info("\nPrivComplianceAgent test finished.")

if __name__ == '__main__':
    asyncio.run(main_compliance_agent_test())
