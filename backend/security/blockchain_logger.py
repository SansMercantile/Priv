# backend/security/blockchain_logger.py
# Implements a logger for recording critical events to a blockchain for immutability.

import logging
import json
from web3 import Web3
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class BlockchainLogger:
    """
    Provides an interface to log data to an Ethereum-compatible blockchain.
    
    This is a conceptual implementation. It requires:
    - A running Ethereum node (e.g., Geth, Infura).
    - An account with ETH to pay for gas.
    - The ABI and address of a deployed smart contract for logging.
    """
    def __init__(self, provider_url: str, private_key: str, contract_address: str, contract_abi: Dict[str, Any]):
        try:
            self.w3 = Web3(Web3.HTTPProvider(provider_url))
            if not self.w3.is_connected():
                raise ConnectionError(f"Could not connect to Ethereum node at {provider_url}")
            
            self.account = self.w3.eth.account.from_key(private_key)
            self.w3.eth.default_account = self.account.address
            self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
            logger.info(f"BlockchainLogger connected to {provider_url}, using account {self.account.address} and contract {contract_address}.")
        except Exception as e:
            logger.critical(f"Failed to initialize BlockchainLogger: {e}", exc_info=True)
            self.w3 = None
            self.contract = None

    def is_available(self) -> bool:
        """Check if the logger is properly initialized and connected."""
        return self.w3 is not None and self.contract is not None and self.w3.is_connected()

    def log_event(self, event_type: str, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Logs an event to the smart contract.
        
        Args:
            event_type: A string identifying the type of event (e.g., "ARBITRATION_DECISION").
            event_data: A JSON-serializable dictionary with the event details.
            
        Returns:
            The transaction hash if successful, otherwise None.
        """
        if not self.is_available():
            logger.error("BlockchainLogger is not available. Cannot log event.")
            return None
            
        try:
            event_data_json = json.dumps(event_data, sort_keys=True)
            
            # Assume the smart contract has a function like:
            # function logEvent(string memory eventType, string memory eventData) public {}
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            tx = self.contract.functions.logEvent(
                event_type,
                event_data_json
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 2000000, # This needs to be estimated properly
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            tx_hash_hex = tx_hash.hex()
            logger.info(f"Submitted event '{event_type}' to blockchain. Transaction hash: {tx_hash_hex}")
            return tx_hash_hex
            
        except Exception as e:
            logger.error(f"Failed to log event to blockchain: {e}", exc_info=True)
            return None

# --- Example Smart Contract ABI ---
# This would be generated from your compiled Solidity contract.
CONCEPTUAL_LOGGING_CONTRACT_ABI = json.loads("""
[
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "address",
				"name": "sender",
				"type": "address"
			},
			{
				"indexed": true,
				"internalType": "string",
				"name": "eventType",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "string",
				"name": "eventData",
				"type": "string"
			}
		],
		"name": "EventLogged",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "eventType",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "eventData",
				"type": "string"
			}
		],
		"name": "logEvent",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	}
]
""")