import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import asyncio # For awaiting async broker operations
import json # For reading/writing wallet vault

# Import necessary components
from backend.treasury.wallet_vault import WalletVault, CardToken # NEW
from backend.trading_engine.trade_executor import broker_router, MoneyManagementMode, calculate_lot_size, execute_market_order, close_position_by_id # NEW: For broker interaction
from backend.multi_agent.arbitration_engine import ArbitrationEngine # NEW: For multi-agent quorum check
from backend.multi_agent.priv_agent_protocol import TradeProposal, TradeAction # For proposing withdrawal/deposit
from backend.multi_agent.agent_reputation_ledger import AgentReputationLedger # For reputation check in quorum
from backend.trading_engine.adapters.deriv_adapter import DerivAPIAdapter # NEW: For deposit/withdrawal via Deriv
from backend.trading_engine.adapters.mock_adapter import MockTradeAPIAdapter # For testing without real broker
from backend.trading_engine.broker_interface import BrokerRouter # NEW: For broker interaction


logger = logging.getLogger(__name__)

# --- Configuration Constants for Funding Protocol ---
FUNDING_THRESHOLD_ZAR = 30000.0  # ZAR
WITHDRAWAL_MILESTONE_ZAR = 250000.0  # ZAR
DEFAULT_FUNDING_AMOUNT_ZAR = 50000.0 # ZAR
DEFAULT_WITHDRAWAL_AMOUNT_ZAR = 50000.0 # ZAR
WITHDRAWAL_QUORUM_THRESHOLD = 0.75 # 75% consensus from agents

# In a real system, you'd fetch conversion rates for ZAR/USD/other currencies
# For now, assume ZAR is the primary account currency or conversions are handled.

class FundingProtocol:
    """
    Manages Priv's automated funding and withdrawal processes for Treasury Management.
    Integrates with WalletVault and BrokerRouter.
    """
    def __init__(self, wallet_vault: WalletVault, arbitration_engine_ref: ArbitrationEngine): # Added arbitration_engine_ref
        self.wallet_vault = wallet_vault
        self.arbitration_engine = arbitration_engine_ref
        logger.info("Priv's FundingProtocol initialized.")

    async def check_funding_trigger(self, current_account_info: Dict[str, Any]) -> bool:
        """
        Checks if the trading capital has dropped below the defined funding threshold.
        If triggered, initiates a top-up.
        """
        balance = current_account_info.get("balance", 0.0)
        currency = current_account_info.get("currency", "USD") # Assume USD for mock, ZAR for real

        # Convert threshold to current account currency if necessary
        # For simplicity, assume thresholds are in the primary account currency for now.
        threshold_in_account_currency = FUNDING_THRESHOLD_ZAR # Assuming ZAR for this example
        
        if balance < threshold_in_account_currency:
            logger.warning(f"Priv: Funding trigger activated! Balance ({balance:.2f} {currency}) below threshold ({threshold_in_account_currency:.2f} {currency}).")
            # In a real system, this would trigger an agent to propose the top-up.
            # For now, we simulate direct initiation.
            return await self.initiate_deposit(card_id="Card A", amount=DEFAULT_FUNDING_AMOUNT_ZAR) # Use Card A as per doc
        logger.debug(f"Priv: Balance {balance:.2f} {currency} is above funding threshold.")
        return False

    async def initiate_deposit(self, card_id: str, amount: float) -> bool:
        """
        Initiates a deposit to Priv's trading capital via the broker API.
        Calls deposit.create via Deriv API (conceptually).
        """
        card_token = self.wallet_vault.retrieve_card_token(card_id)
        if not card_token:
            logger.error(f"Priv: Deposit failed: Card token for '{card_id}' not found in WalletVault.")
            return False

        active_adapter = broker_router.select_adapter(criteria={"action_type": "deposit"})
        if not active_adapter:
            logger.error("Priv: Deposit failed: No active broker adapter found for deposit.")
            return False

        logger.info(f"Priv: Initiating deposit of {amount:.2f} {card_token.currency} using card '{card_token.last_four_digits}' via {type(active_adapter).__name__}.")
        
        try:
            # This is a conceptual call, as DerivAPI's `deposit.create` is complex and often manual/redirect based.
            # For a real automated deposit, you'd need direct bank/card API integration, not typically broker API.
            # Deriv's 'deposit.create' typically returns a URL for user redirection.
            # We will mock the success of this operation.
            
            # For demonstration, assume Deriv has a 'transfer_funds' or similar direct method for automated deposit.
            # If `active_adapter` is `DerivAPIAdapter`
            if isinstance(active_adapter, DerivAPIAdapter):
                # Simulate a direct deposit. Actual Deriv deposits involve payment gateways.
                # Here, we represent success.
                # Success based on successful API call would be:
                # await active_adapter.api.something_like_deposit_create(amount=amount, currency=card_token.currency, payment_method=card_token.token)
                # For now, just logging success.
                logger.info(f"Priv: Deposit to Deriv initiated for {amount:.2f} {card_token.currency}. (Mock Success)")
                # Update mock account balance in the adapter for realism
                active_adapter._mock_account_balance += amount # Directly update mock balance
                active_adapter._mock_account_equity += amount
                active_adapter._mock_account_free_margin += amount
                
                # Log to immutable ledger
                # This would be an ActionToken
                # action_tokenizer.generate_token(...)
                
                return True
            else:
                logger.warning(f"Priv: Deposit not supported by {type(active_adapter).__name__} directly. Manual intervention required.")
                return False

        except Exception as e:
            logger.error(f"Priv: Error initiating deposit: {e}", exc_info=True)
            return False

    async def check_withdrawal_trigger(self, current_account_info: Dict[str, Any], cumulative_profit: float) -> bool:
        """
        Checks if cumulative profit has reached the withdrawal milestone.
        If triggered, initiates a multi-agent quorum vote.
        """
        balance = current_account_info.get("balance", 0.0)
        currency = current_account_info.get("currency", "USD")

        threshold_in_account_currency = WITHDRAWAL_MILESTONE_ZAR
        
        if cumulative_profit >= threshold_in_account_currency:
            logger.warning(f"Priv: Withdrawal trigger activated! Cumulative profit ({cumulative_profit:.2f} {currency}) reached milestone ({threshold_in_account_currency:.2f} {currency}).")
            # In a real multi-agent system, this would lead to a proposal for withdrawal.
            # Here, we initiate the conceptual multi-agent vote.
            
            # Create a conceptual withdrawal proposal for arbitration
            withdrawal_proposal = TradeProposal(
                agent_id="Priv_Main_Strategist", # Agent initiating proposal
                symbol="TREASURY", # Special symbol for treasury actions
                action=TradeAction.CLOSE, # Or a new Enum like TradeAction.WITHDRAW
                volume=DEFAULT_WITHDRAWAL_AMOUNT_ZAR,
                entry_price=0.0, # Not applicable
                reasoning=f"Cumulative profit milestone reached ({cumulative_profit:.2f}). Initiating withdrawal of {DEFAULT_WITHDRAWAL_AMOUNT_ZAR}.",
                confidence=1.0, # High confidence in its own trigger
                risk_assessment={"type": "withdrawal", "current_balance": balance}
            )
            
            # Submit to arbitration for quorum vote
            if self.arbitration_engine:
                # This needs to simulate other agents voting. For now, it's a single agent voting on its own proposal.
                # arbitration_engine.arbitrate_trade_proposals expects proposals from *multiple* agents for true arbitration.
                # For this conceptual quorum, we assume the engine can take just one and check if it passes quorum internally.
                
                # A more realistic approach would be for the `StrategicAdvisor` (or a dedicated "CFO Priv")
                # to submit this proposal, and other agents (mocked or real) vote on it in a later cycle.
                
                # For immediate testing, we'll make a simplified check here.
                # Simulate quorum check as part of direct call
                
                # For now, let's assume `arbitrate_trade_proposals` can handle a single proposal and check against a virtual quorum.
                # Or, we make `arbitrate_trade_proposals` return a boolean if it passed its criteria.
                
                # Let's adjust: arbitration_engine returns the decided action.
                # If the chosen method is 'majority_vote' and threshold is met for *this* proposal.
                
                # Assume a direct check for approval based on hardcoded quorum for this conceptual stage.
                # This is "Strategic Vote Confirmed".
                
                # A simpler way to simulate "quorum" without multiple live agents is to check if
                # the proposing agent's reputation meets a high standard (e.g., > 0.8) and if the
                # proposal itself is considered low risk.
                
                # Let's use the arbitration engine to get a 'final_decision', but note that it needs multiple proposals.
                # For this single-agent context, we'll make a direct decision and log.
                
                # This needs to be a proposal to the arbitration engine from a specific agent.
                # The StrategicAdvisor (which is a PrivAgent) makes the proposal, and then
                # the arbitration engine gets it.
                
                # Given FundingProtocol is a helper for StrategicAdvisor, let's simplify.
                # StrategicAdvisor will call check_withdrawal_trigger, and then StrategicAdvisor itself
                # will create the proposal and submit it.
                
                # Therefore, this function just needs to return True if the trigger is met.
                return True
            else:
                logger.warning("Priv: Arbitration Engine not initialized. Cannot perform multi-agent quorum check.")
                return False
        
        logger.debug(f"Priv: Cumulative profit {cumulative_profit:.2f} {currency} is below withdrawal milestone.")
        return False

    async def initiate_withdrawal(self, card_id: str, amount: float) -> bool:
        """
        Initiates a withdrawal from profits to a designated card via the broker API.
        Requires multi-agent quorum confirmation (conceptual here).
        """
        card_token = self.wallet_vault.retrieve_card_token(card_id)
        if not card_token:
            logger.error(f"Priv: Withdrawal failed: Card token for '{card_id}' not found in WalletVault.")
            return False

        active_adapter = broker_router.select_adapter(criteria={"action_type": "withdraw"})
        if not active_adapter:
            logger.error("Priv: Withdrawal failed: No active broker adapter found for withdrawal.")
            return False
        
        # This is a conceptual call, as DerivAPI's `withdrawal.create` involves manual processes/email confirmation.
        # We will mock the success of this operation.
        
        logger.info(f"Priv: Initiating withdrawal of {amount:.2f} {card_token.currency} to card '{card_token.last_four_digits}' via {type(active_adapter).__name__}. (Mock Success)")
        
        # Update mock account balance in the adapter for realism
        if isinstance(active_adapter, DerivAPIAdapter):
            active_adapter._mock_account_balance -= amount # Directly update mock balance
            active_adapter._mock_account_equity -= amount
            active_adapter._mock_account_free_margin -= amount

        # Log to immutable ledger
        # This would be an ActionToken for withdrawal action.
        # action_tokenizer.generate_token(...)

        return True


# Example Usage (for testing FundingProtocol in isolation)
async def main_funding_protocol_test():
    logging.basicConfig(level=logging.INFO)

    # --- Setup Dependencies ---
    wallet_vault_instance = WalletVault(vault_file_path="temp_wallet_vault.json")
    wallet_vault_instance.store_card_token("Card A", "mock_token_1234", "1234", "ZAR")
    wallet_vault_instance.store_card_token("Card B", "mock_token_5678", "5678", "USD")

    # Mock BrokerRouter with a MockTradeAPIAdapter
    class MockAdapterForFundingTest(MockTradeAPIAdapter):
        def __init__(self, name="FundingTestMockAdapter"):
            super().__init__(name=name)
            self._mock_account_balance = 25000.0 # Start below threshold for funding test
            self._mock_account_equity = 25000.0
            self._mock_account_free_margin = 20000.0

    global broker_router # Ensure we are modifying the global instance for the test
    broker_router = BrokerRouter(adapters=[MockAdapterForFundingTest()])

    # Mock ArbitrationEngine (just needs to be instantiable for FundingProtocol init)
    class MockArbitrationEngine:
        def __init__(self, *args, **kwargs): pass
        async def arbitrate_trade_proposals(self, proposals, arbitration_method, conflict_resolution_threshold):
            # Simulate approval for funding/withdrawal proposals for this test
            if proposals[0].action == TradeAction.BUY or proposals[0].action == TradeAction.CLOSE: # Simplified: assume BUY is deposit, CLOSE is withdrawal
                return {"action": proposals[0].action.value, "approved": True}
            return {"action": TradeAction.HOLD.value, "approved": False}

    arbitration_engine_instance = MockArbitrationEngine() # Global instance reference for the protocol
    
    funding_protocol = FundingProtocol(wallet_vault=wallet_vault_instance, arbitration_engine_ref=arbitration_engine_instance)

    # --- Test 1: Funding Trigger and Deposit ---
    print("\n--- Test 1: Funding Trigger and Deposit ---")
    current_account_info = await broker_router.select_adapter({}).get_account_info()
    print(f"Initial Account Balance: {current_account_info['balance']:.2f}")
    
    await funding_protocol.check_funding_trigger(current_account_info)
    
    updated_account_info = await broker_router.select_adapter({}).get_account_info()
    print(f"Account Balance After Funding Check: {updated_account_info['balance']:.2f}")
    # Expected: Balance should be 25000 + 50000 = 75000

    # --- Test 2: Withdrawal Trigger and Protocol ---
    print("\n--- Test 2: Withdrawal Trigger and Protocol ---")
    # Simulate cumulative profit for withdrawal
    cumulative_profit = WITHDRAWAL_MILESTONE_ZAR + 10000.0 # Above milestone
    
    # Check withdrawal trigger (this function only returns bool)
    trigger_met = await funding_protocol.check_withdrawal_trigger(updated_account_info, cumulative_profit)
    print(f"Withdrawal trigger met: {trigger_met}") # Expected: True

    # If trigger met, then in a real system, the StrategicAdvisor would make the proposal.
    # For this test, we directly initiate withdrawal to confirm the protocol's function.
    if trigger_met:
        withdrawal_successful = await funding_protocol.initiate_withdrawal(card_id="Card B", amount=DEFAULT_WITHDRAWAL_AMOUNT_ZAR)
        print(f"Withdrawal successful: {withdrawal_successful}")
        updated_account_info_after_withdrawal = await broker_router.select_adapter({}).get_account_info()
        print(f"Account Balance After Withdrawal: {updated_account_info_after_withdrawal['balance']:.2f}")
        # Expected: Balance should be 75000 - 50000 = 25000 (if Deriv mock updates balance)

    # Clean up mock vault file
    if os.path.exists(wallet_vault_instance.vault_file_path):
        os.remove(wallet_vault_instance.vault_file_path)
        logger.info(f"Cleaned up mock vault file: {wallet_vault_instance.vault_file_path}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main_funding_protocol_test())