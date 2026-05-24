"""
PayPal Payment Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Handles all PayPal payment processing and subscription management.
"""

import os
import logging
from typing import Dict, Optional, Any
import requests
from datetime import datetime
import base64

logger = logging.getLogger(__name__)


class PayPalIntegration:
    """
    PayPal payment integration for PRIV.
    
    Handles:
    - Payment processing
    - Subscription management
    - Webhook handling
    """
    
    def __init__(self):
        self.client_id = os.getenv("PAYPAL_CLIENT_ID", "")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET", "")
        self.mode = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox or live
        
        if self.mode == "sandbox":
            self.base_url = "https://api-m.sandbox.paypal.com"
        else:
            self.base_url = "https://api-m.paypal.com"
        
        self.access_token = None
        self.token_expiry = None
    
    async def _get_access_token(self) -> str:
        """
        Get PayPal access token.
        
        Returns:
            Access token
        """
        # Check if token is still valid
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token
        
        # Get new token
        try:
            auth = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            
            headers = {
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {"grant_type": "client_credentials"}
            
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                headers=headers,
                data=data
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            # Token expires in seconds, set expiry to 90% of that time
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in * 0.9)
            
            logger.info("Obtained PayPal access token")
            return self.access_token
            
        except requests.RequestException as e:
            logger.error(f"Failed to get PayPal access token: {e}")
            raise
    
    async def create_order(
        self,
        amount: float,
        currency: str,
        description: Optional[str] = None,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a PayPal order.
        
        Args:
            amount: Amount in dollars
            currency: Currency code (USD, EUR, etc.)
            description: Order description
            return_url: URL to return to after approval
            cancel_url: URL to return to on cancel
            
        Returns:
            Order object
        """
        try:
            token = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}"
                    },
                    "description": description or "PRIV Payment"
                }],
                "application_context": {
                    "return_url": return_url or "https://priv.com/payment/success",
                    "cancel_url": cancel_url or "https://priv.com/payment/cancel"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders",
                headers=headers,
                json=order_data
            )
            
            response.raise_for_status()
            order = response.json()
            
            # Get approval URL
            approval_url = None
            for link in order.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            logger.info(f"Created PayPal order: {order['id']}")
            
            return {
                "order_id": order["id"],
                "status": order["status"],
                "approval_url": approval_url,
                "amount": amount,
                "currency": currency
            }
            
        except requests.RequestException as e:
            logger.error(f"PayPal order creation failed: {e}")
            raise
    
    async def capture_order(
        self,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Capture a PayPal order.
        
        Args:
            order_id: PayPal order ID
            
        Returns:
            Capture result
        """
        try:
            token = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers=headers
            )
            
            response.raise_for_status()
            capture = response.json()
            
            logger.info(f"Captured PayPal order: {order_id}")
            
            return {
                "order_id": order_id,
                "status": capture["status"],
                "capture_id": capture["purchase_units"][0]["payments"]["captures"][0]["id"]
            }
            
        except requests.RequestException as e:
            logger.error(f"PayPal order capture failed: {e}")
            raise
    
    async def create_subscription(
        self,
        plan_id: str,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a PayPal subscription.
        
        Args:
            plan_id: PayPal plan ID
            return_url: URL to return to after approval
            cancel_url: URL to return to on cancel
            
        Returns:
            Subscription object
        """
        try:
            token = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            subscription_data = {
                "plan_id": plan_id,
                "application_context": {
                    "return_url": return_url or "https://priv.com/subscription/success",
                    "cancel_url": cancel_url or "https://priv.com/subscription/cancel"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/v1/billing/subscriptions",
                headers=headers,
                json=subscription_data
            )
            
            response.raise_for_status()
            subscription = response.json()
            
            # Get approval URL
            approval_url = None
            for link in subscription.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            logger.info(f"Created PayPal subscription: {subscription['id']}")
            
            return {
                "subscription_id": subscription["id"],
                "status": subscription["status"],
                "approval_url": approval_url
            }
            
        except requests.RequestException as e:
            logger.error(f"PayPal subscription creation failed: {e}")
            raise
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel a PayPal subscription.
        
        Args:
            subscription_id: PayPal subscription ID
            reason: Cancellation reason
            
        Returns:
            Cancellation result
        """
        try:
            token = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "reason": reason or "Customer requested cancellation"
            }
            
            response = requests.post(
                f"{self.base_url}/v1/billing/subscriptions/{subscription_id}/cancel",
                headers=headers,
                json=data
            )
            
            response.raise_for_status()
            
            logger.info(f"Cancelled PayPal subscription: {subscription_id}")
            
            return {
                "subscription_id": subscription_id,
                "status": "cancelled"
            }
            
        except requests.RequestException as e:
            logger.error(f"PayPal subscription cancellation failed: {e}")
            raise
    
    async def get_subscription_status(
        self,
        subscription_id: str
    ) -> Dict[str, Any]:
        """
        Get PayPal subscription status.
        
        Args:
            subscription_id: PayPal subscription ID
            
        Returns:
            Subscription status
        """
        try:
            token = await self._get_access_token()
            
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            response = requests.get(
                f"{self.base_url}/v1/billing/subscriptions/{subscription_id}",
                headers=headers
            )
            
            response.raise_for_status()
            subscription = response.json()
            
            return {
                "subscription_id": subscription["id"],
                "status": subscription["status"],
                "start_time": subscription.get("start_time"),
                "next_billing_time": subscription.get("billing_info", {}).get("next_billing_time")
            }
            
        except requests.RequestException as e:
            logger.error(f"PayPal subscription status retrieval failed: {e}")
            raise


from datetime import timedelta

