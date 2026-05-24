"""
PayFast Integration Module
~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration with PayFast payment gateway for South African payments.
Supports one-time payments, recurring billing, and subscriptions.
"""

import logging
import hashlib
import requests
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import uuid
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class PayFastIntegration:
    """PayFast payment gateway integration class."""
    
    def __init__(self, merchant_id: str, merchant_key: str, passphrase: str, sandbox: bool = True):
        """
        Initialize PayFast integration.
        
        Args:
            merchant_id: PayFast merchant ID
            merchant_key: PayFast merchant key
            passphrase: PayFast passphrase for security
            sandbox: Whether to use sandbox environment
        """
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self.passphrase = passphrase
        self.sandbox = sandbox
        
        # PayFast endpoints
        if sandbox:
            self.base_url = "https://sandbox.payfast.co.za/eng/process"
            self.api_url = "https://sandbox.payfast.co.za/eng/api"
        else:
            self.base_url = "https://www.payfast.co.za/eng/process"
            self.api_url = "https://www.payfast.co.za/eng/api"
    
    def generate_signature(self, data: Dict[str, Any]) -> str:
        """
        Generate PayFast signature for security.
        
        Args:
            data: Data to sign
            
        Returns:
            Generated signature string
        """
        # Create a copy of data and remove signature field if present
        data_copy = {k: v for k, v in data.items() if k != 'signature'}
        
        # Sort the data alphabetically by key
        sorted_data = sorted(data_copy.items())
        
        # Create the string to be signed
        signature_string = '&'.join([f'{key}={value}' for key, value in sorted_data if value])
        
        # Add passphrase at the end if provided
        if self.passphrase:
            signature_string += f'&passphrase={self.passphrase}'
        
        # Generate MD5 hash
        signature = hashlib.md5(signature_string.encode()).hexdigest()
        
        logger.debug(f"Generated signature: {signature}")
        return signature
    
    def create_payment_request(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a payment request for one-time payment.
        
        Args:
            payment_data: Dictionary containing payment details
                - amount: Payment amount
                - item_name: Description of item
                - item_description: Detailed description
                - return_url: URL to return after payment
                - cancel_url: URL to return on cancellation
                - notify_url: ITN notification URL
                - custom_str1: Custom data (optional)
                - custom_str2: Custom data (optional)
                - custom_str3: Custom data (optional)
                - custom_str4: Custom data (optional)
                - custom_str5: Custom data (optional)
        
        Returns:
            Dictionary with payment URL and parameters
        """
        # Required fields
        data = {
            'merchant_id': self.merchant_id,
            'merchant_key': self.merchant_key,
            'return_url': payment_data.get('return_url', ''),
            'cancel_url': payment_data.get('cancel_url', ''),
            'notify_url': payment_data.get('notify_url', ''),
            'name_first': payment_data.get('name_first', ''),
            'name_last': payment_data.get('name_last', ''),
            'email_address': payment_data.get('email_address', ''),
            'm_payment_id': payment_data.get('m_payment_id', str(uuid.uuid4())),
            'amount': f"{float(payment_data['amount']):.2f}",
            'item_name': payment_data['item_name'],
            'item_description': payment_data.get('item_description', ''),
        }
        
        # Add custom fields if provided
        for i in range(1, 6):
            key = f'custom_str{i}'
            if key in payment_data:
                data[key] = payment_data[key]
        
        # Generate signature
        data['signature'] = self.generate_signature(data)
        
        # Generate payment URL
        payment_url = f"{self.base_url}?{urlencode(data)}"
        
        logger.info(f"Created PayFast payment request: {payment_url[:100]}...")
        
        return {
            'payment_url': payment_url,
            'm_payment_id': data['m_payment_id'],
            'signature': data['signature']
        }
    
    def create_subscription(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a recurring subscription.
        
        Args:
            subscription_data: Dictionary containing subscription details
                - amount: Recurring payment amount
                - item_name: Subscription plan name
                - item_description: Subscription description
                - billing_date: Initial billing date (YYYY-MM-DD)
                - frequency: Billing frequency (3=monthly, 4=quarterly, 5=biannual, 6=annual)
                - cycles: Number of payment cycles (0 for indefinite)
                - return_url: URL to return after subscription setup
                - cancel_url: URL to return on cancellation
                - notify_url: ITN notification URL
        
        Returns:
            Dictionary with subscription URL and token
        """
        # Required fields
        data = {
            'merchant_id': self.merchant_id,
            'merchant_key': self.merchant_key,
            'return_url': subscription_data.get('return_url', ''),
            'cancel_url': subscription_data.get('cancel_url', ''),
            'notify_url': subscription_data.get('notify_url', ''),
            'name_first': subscription_data.get('name_first', ''),
            'name_last': subscription_data.get('name_last', ''),
            'email_address': subscription_data.get('email_address', ''),
            'm_payment_id': subscription_data.get('m_payment_id', str(uuid.uuid4())),
            'amount': f"{float(subscription_data['amount']):.2f}",
            'item_name': subscription_data['item_name'],
            'item_description': subscription_data.get('item_description', ''),
            'subscription_type': '1',  # Recurring subscription
            'billing_date': subscription_data.get('billing_date', ''),
            'frequency': subscription_data.get('frequency', '3'),  # Default monthly
            'cycles': subscription_data.get('cycles', '0'),  # Default indefinite
        }
        
        # Generate signature
        data['signature'] = self.generate_signature(data)
        
        # Generate subscription URL
        subscription_url = f"{self.base_url}?{urlencode(data)}"
        
        logger.info(f"Created PayFast subscription: {subscription_url[:100]}...")
        
        return {
            'subscription_url': subscription_url,
            'token': data['m_payment_id'],
            'signature': data['signature']
        }
    
    def verify_itn(self, itn_data: Dict[str, Any]) -> bool:
        """
        Verify Instant Transaction Notification (ITN) from PayFast.
        
        Args:
            itn_data: ITN data received from PayFast
            
        Returns:
            True if ITN is valid, False otherwise
        """
        try:
            # Extract received signature
            received_signature = itn_data.get('signature', '')
            
            # Generate our own signature
            expected_signature = self.generate_signature(itn_data)
            
            # Compare signatures
            if received_signature != expected_signature:
                logger.error("ITN signature verification failed")
                return False
            
            # Additional validation can be added here
            # For example, validate payment status, amount, etc.
            
            logger.info("ITN verification successful")
            return True
            
        except Exception as e:
            logger.error(f"ITN verification error: {str(e)}")
            return False
    
    def fetch_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch transaction details from PayFast API.
        
        Args:
            transaction_id: PayFast transaction ID
            
        Returns:
            Transaction details or None if failed
        """
        try:
            # Prepare request data
            data = {
                'merchant_id': self.merchant_id,
                'merchant_key': self.merchant_key,
            }
            
            # Generate signature for API request
            signature = self.generate_signature(data)
            data['signature'] = signature
            
            # Make API request
            response = requests.get(
                f"{self.api_url}/transactions/{transaction_id}",
                params=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                transaction_data = response.json()
                logger.info(f"Fetched transaction {transaction_id} successfully")
                return transaction_data
            else:
                logger.error(f"Failed to fetch transaction: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching transaction: {str(e)}")
            return None
    
    def cancel_subscription(self, subscription_token: str) -> bool:
        """
        Cancel a PayFast subscription.
        
        Args:
            subscription_token: PayFast subscription token
            
        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            # Prepare request data
            data = {
                'merchant_id': self.merchant_id,
                'merchant_key': self.merchant_key,
                'token': subscription_token,
            }
            
            # Generate signature
            signature = self.generate_signature(data)
            data['signature'] = signature
            
            # Make API request
            response = requests.post(
                f"{self.api_url}/subscriptions/cancel",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    logger.info(f"Cancelled subscription {subscription_token} successfully")
                    return True
            
            logger.error(f"Failed to cancel subscription: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return False
    
    def get_subscription_status(self, subscription_token: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a PayFast subscription.
        
        Args:
            subscription_token: PayFast subscription token
            
        Returns:
            Subscription status or None if failed
        """
        try:
            # Prepare request data
            data = {
                'merchant_id': self.merchant_id,
                'merchant_key': self.merchant_key,
                'token': subscription_token,
            }
            
            # Generate signature
            signature = self.generate_signature(data)
            data['signature'] = signature
            
            # Make API request
            response = requests.get(
                f"{self.api_url}/subscriptions/status",
                params=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                status_data = response.json()
                logger.info(f"Fetched subscription status for {subscription_token}")
                return status_data
            else:
                logger.error(f"Failed to fetch subscription status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching subscription status: {str(e)}")
            return None
    
    def process_refund(self, transaction_id: str, amount: float) -> bool:
        """
        Process a refund for a transaction.
        
        Args:
            transaction_id: PayFast transaction ID to refund
            amount: Amount to refund
            
        Returns:
            True if refund successful, False otherwise
        """
        try:
            # Prepare request data
            data = {
                'merchant_id': self.merchant_id,
                'merchant_key': self.merchant_key,
                'pf_transaction_id': transaction_id,
                'amount': f"{amount:.2f}",
            }
            
            # Generate signature
            signature = self.generate_signature(data)
            data['signature'] = signature
            
            # Make API request
            response = requests.post(
                f"{self.api_url}/refunds",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    logger.info(f"Processed refund for transaction {transaction_id}")
                    return True
            
            logger.error(f"Failed to process refund: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            return False