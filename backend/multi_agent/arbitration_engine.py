# backend/multi_agent/arbitration_engine.py

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import asyncio

# Import project components
from backend.multi_agent.priv_agent_protocol import TradeProposal, TradeAction
from backend.multi_agent.agent_reputation_ledger import AgentReputationLedger
from backend.governance.ethical_framework import EthicalStatus
from backend.governance.tokenization.zk_verifier import ZKVerifier
from backend.security.blockchain_logger import BlockchainLogger, CONCEPTUAL_LOGGING_CONTRACT_ABI
from backend.config import settings

logger = logging.getLogger(__name__)

class ArbitrationEngine:
    """
    Manages arbitration between multiple Priv Agents for trade decision-making.
    This version uses real, non-conceptual integrations with other modules.
    """
    def __init__(self,
                 reputation_ledger: AgentReputationLedger,
                 zk_verifier: ZKVerifier):
        self.reputation_ledger = reputation_ledger
        self.zk_verifier = zk_verifier
        self.blockchain_logger: Optional[BlockchainLogger] = None

        # Initialize BlockchainLogger with configuration from settings
        if all([settings.BLOCKCHAIN_PROVIDER_URL, settings.BLOCKCHAIN_LOGGER_PRIVATE_KEY, settings.BLOCKCHAIN_LOGGER_CONTRACT_ADDRESS]):
            self.blockchain_logger = BlockchainLogger(
                provider_url=settings.BLOCKCHAIN_PROVIDER_URL,
                private_key=settings.BLOCKCHAIN_LOGGER_PRIVATE_KEY,
                contract_address=settings.BLOCKCHAIN_LOGGER_CONTRACT_ADDRESS,
                contract_abi=CONCEPTUAL_LOGGING_CONTRACT_ABI
            )
            if self.blockchain_logger.is_available():
                logger.info("ArbitrationEngine initialized with active BlockchainLogger.")
            else:
                logger.error("ArbitrationEngine: BlockchainLogger failed to connect or initialize. It will be disabled.")
                self.blockchain_logger = None
        else:
            logger.warning("ArbitrationEngine initialized without complete blockchain logger configuration. It will be disabled.")


    def _ethical_delta_resolver(self, proposals: List[TradeProposal]) -> bool:
        """
        Checks for any critical ethical violations in the proposals.
        Returns True if a critical violation is found, otherwise False.
        """
        for proposal in proposals:
            ethical_status = proposal.risk_assessment.get("ethical_check", {}).get("status")
            if ethical_status == EthicalStatus.NON_COMPLIANT.value:
                logger.warning(f"Ethical Delta Resolver detected a non-compliant ethical status in proposal from {proposal.agent_id}.")
                return True
        return False

    def arbitrate_trade_proposals(
        self,
        proposals: List[TradeProposal],
        arbitration_method: str = "weighted_confidence",
        conflict_resolution_threshold: float = 0.6
    ) -> Optional[Dict[str, Any]]:
        """
        Arbitrates a list of trade proposals to arrive at a single decision.
        """
        if not proposals:
            logger.info("No proposals received for arbitration.")
            return None

        # If only one proposal, it wins by default after a basic check.
        if len(proposals) == 1:
            if not self._ethical_delta_resolver(proposals):
                final_decision = proposals[0].model_dump()
                self._log_final_decision(final_decision, proposals)
                return final_decision
            else:
                return self.resolve_conflict(proposals, "ethical_violation")

        # Preliminary check for critical ethical violations
        if self._ethical_delta_resolver(proposals):
            return self.resolve_conflict(proposals, "ethical_violation")

        # Group proposals by the action they propose (e.g., all BUY EURUSD proposals together)
        grouped_proposals: Dict[Tuple[str, str], List[TradeProposal]] = {}
        for p in proposals:
            key = (p.action.value, p.symbol)
            grouped_proposals.setdefault(key, []).append(p)

        # Calculate a score for each group based on weighted confidence
        scored_groups = []
        for (action, symbol), group in grouped_proposals.items():
            total_weighted_confidence = 0.0
            for p in group:
                agent_rep = self.reputation_ledger.get_reputation_score(p.agent_id)
                total_weighted_confidence += p.confidence * agent_rep
            
            scored_groups.append({
                "action": action,
                "symbol": symbol,
                "score": total_weighted_confidence,
                "proposals": group
            })
        
        # If no groups, something went wrong.
        if not scored_groups:
            return self.resolve_conflict(proposals, "no_valid_groups")

        # Determine the winning group
        winning_group = max(scored_groups, key=lambda x: x['score'])
        
        # Simple conflict resolution: if there's only one group, it wins.
        # If multiple groups, the highest score wins. A more advanced system
        # could check the margin of victory.
        final_decision_dict = max(winning_group['proposals'], key=lambda p: p.confidence).model_dump()
        final_decision_dict['arbitration_outcome'] = 'CONSENSUS_REACHED'
        final_decision_dict['arbitration_score'] = winning_group['score']
        
        self._log_final_decision(final_decision_dict, proposals)
        return final_decision_dict


    def resolve_conflict(self, proposals: List[TradeProposal], reason: str) -> Dict[str, Any]:
        """
        Resolves conflicts by issuing a 'HOLD' signal and logs the event.
        """
        logger.warning(f"Conflict detected among proposals. Reason: {reason}. Issuing HOLD.")
        default_symbol = proposals[0].symbol if proposals else "N/A"
        
        conflict_decision = {
            "symbol": default_symbol,
            "action": TradeAction.HOLD.value,
            "volume": 0.0,
            "confidence": 0.0,
            "reasoning": f"No consensus or critical conflict. Reason: {reason}.",
            "arbitration_outcome": "CONFLICT_HOLD"
        }
        self._log_final_decision(conflict_decision, proposals)
        return conflict_decision

    def _log_final_decision(self, decision: Optional[Dict[str, Any]], proposals: List[TradeProposal]):
        """Helper function to log the final decision to the blockchain asynchronously."""
        if not (decision and self.blockchain_logger and self.blockchain_logger.is_available()):
            return

        # Create a unique, deterministic hash of the input proposals
        proposal_hashes = "".join(sorted([p.model_dump_json() for p in proposals]))
        input_hash = hashlib.sha256(proposal_hashes.encode()).hexdigest()
        
        log_data = {
            "decision": decision,
            "proposals_input_hash": input_hash,
            "timestamp_utc": datetime.utcnow().isoformat(),
        }
        
        # Run the blocking blockchain call in a separate thread
        asyncio.create_task(self._log_to_blockchain_thread_safe("ARBITRATION_DECISION", log_data))

    async def _log_to_blockchain_thread_safe(self, event_type: str, data: dict):
        """Asynchronous wrapper to call the blocking blockchain logger."""
        loop = asyncio.get_running_loop()
        try:
            tx_hash = await loop.run_in_executor(
                None,  # Uses the default thread pool executor
                self.blockchain_logger.log_event,
                event_type,
                data
            )
            if tx_hash:
                logger.info(f"Successfully submitted decision to blockchain. Tx Hash: {tx_hash}")
            else:
                logger.error("Failed to submit decision to blockchain (tx_hash is None).")
        except Exception as e:
            logger.error(f"Exception while logging to blockchain: {e}", exc_info=True)
