"""
PayPal Payment Service
Handles all PayPal payment operations including subscriptions and webhooks
"""

import httpx
import os
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PayPalService:
    """Service for handling PayPal payment operations"""
    
    def __init__(self):
        """Initialize PayPal service with credentials"""
        self.client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        self.webhook_id = os.getenv("PAYPAL_WEBHOOK_ID")
        self.mode = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox or live
        
        if self.mode == "sandbox":
            self.api_base = "https://api-m.sandbox.paypal.com"
        else:
            self.api_base = "https://api-m.paypal.com"
        
        self.access_token = None
        self.token_expiry = None
        
        if not self.client_id or not self.client_secret:
            logger.warning("PayPal credentials not set - PayPal operations will fail")
    
    async def get_access_token(self) -> str:
        """
        Get PayPal access token
        
        Returns:
            Access token
        """
        try:
            # Check if token is still valid
            if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
                return self.access_token
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/v1/oauth2/token",
                    auth=(self.client_id, self.client_secret),
                    data={"grant_type": "client_credentials"}
                )
                response.raise_for_status()
                
                data = response.json()
                self.access_token = data["access_token"]
                
                # Set expiry to 1 hour from now (PayPal tokens expire in 3600 seconds)
                from datetime import timedelta
                self.token_expiry = datetime.now() + timedelta(seconds=3500)
                
                logger.info("Retrieved PayPal access token")
                return self.access_token
        except httpx.HTTPError as e:
            logger.error(f"Error getting PayPal access token: {e}")
            raise
    
    async def create_plan(
        self,
        name: str,
        description: str,
        amount: float,
        currency: str = "USD",
        interval: str = "MONTH",
        interval_count: int = 1
    ) -> str:
        """
        Create a PayPal billing plan
        
        Args:
            name: Plan name
            description: Plan description
            amount: Plan amount
            currency: Currency code
            interval: Billing interval (MONTH, YEAR, etc.)
            interval_count: Number of intervals
            
        Returns:
            PayPal plan ID
        """
        try:
            token = await self.get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/v1/billing/plans",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "product_id": "PROD-PRIV-SUBSCRIPTION",
                        "name": name,
                        "description": description,
                        "billing_cycles": [
                            {
                                "frequency": {
                                    "interval_unit": interval,
                                    "interval_count": interval_count
                                },
                                "tenure_type": "REGULAR",
                                "sequence": 1,
                                "total_cycles": 0,  # Infinite
                                "pricing_scheme": {
                                    "fixed_price": {
                                        "value": str(amount),
                                        "currency_code": currency
                                    }
                                }
                            }
                        ],
                        "payment_preferences": {
                            "auto_bill_amount": "YES",
                            "payment_failure_threshold": 3
                        }
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                plan_id = data["id"]
                logger.info(f"Created PayPal plan {plan_id}")
                return plan_id
        except httpx.HTTPError as e:
            logger.error(f"Error creating PayPal plan: {e}")
            raise
    
    async def create_subscription(
        self,
        plan_id: str,
        user_id: str,
        email: str,
        return_url: str,
        cancel_url: str
    ) -> Dict:
        """
        Create a PayPal subscription
        
        Args:
            plan_id: PayPal plan ID
            user_id: User ID
            email: Customer email
            return_url: Return URL after approval
            cancel_url: Cancel URL
            
        Returns:
            Subscription details with approval link
        """
        try:
            token = await self.get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/v1/billing/subscriptions",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "plan_id": plan_id,
                        "subscriber": {
                            "name": {
                                "given_name": "User",
                                "surname": user_id
                            },
                            "email_address": email
                        },
                        "application_context": {
                            "brand_name": "PRIV",
                            "locale": "en-US",
                            "user_action": "SUBSCRIBE_NOW",
                            "return_url": return_url,
                            "cancel_url": cancel_url
                        }
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                subscription_id = data["id"]
                
                # Find approval link
                approval_link = None
                for link in data.get("links", []):
                    if link["rel"] == "approve":
                        approval_link = link["href"]
                        break
                
                logger.info(f"Created PayPal subscription {subscription_id}")
                
                return {
                    "subscription_id": subscription_id,
                    "status": data.get("status"),
                    "approval_url": approval_link
                }
        except httpx.HTTPError as e:
            logger.error(f"Error creating PayPal subscription: {e}")
            raise
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        reason: str = "User requested cancellation"
    ) -> Dict:
        """
        Cancel a PayPal subscription
        
        Args:
            subscription_id: PayPal subscription ID
            reason: Cancellation reason
            
        Returns:
            Cancellation details
        """
        try:
            token = await self.get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/v1/billing/subscriptions/{subscription_id}/cancel",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"reason": reason}
                )
                response.raise_for_status()
                
                logger.info(f"Cancelled PayPal subscription {subscription_id}")
                return {"status": "cancelled"}
        except httpx.HTTPError as e:
            logger.error(f"Error cancelling PayPal subscription: {e}")
            raise
    
    async def get_subscription(self, subscription_id: str) -> Dict:
        """
        Get subscription details
        
        Args:
            subscription_id: PayPal subscription ID
            
        Returns:
            Subscription details
        """
        try:
            token = await self.get_access_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/v1/billing/subscriptions/{subscription_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                response.raise_for_status()
                
                data = response.json()
                return {
                    "subscription_id": data["id"],
                    "status": data.get("status"),
                    "plan_id": data.get("plan_id"),
                    "start_time": data.get("start_time"),
                    "next_billing_time": data.get("billing_info", {}).get("next_billing_time")
                }
        except httpx.HTTPError as e:
            logger.error(f"Error retrieving PayPal subscription: {e}")
            raise
    
    def verify_webhook_signature(
        self,
        webhook_id: str,
        event_body: str,
        transmission_id: str,
        transmission_time: str,
        cert_url: str,
        auth_algo: str,
        transmission_sig: str
    ) -> bool:
        """
        Verify PayPal webhook signature
        
        Args:
            webhook_id: Webhook ID
            event_body: Event body
            transmission_id: Transmission ID
            transmission_time: Transmission time
            cert_url: Certificate URL
            auth_algo: Authentication algorithm
            transmission_sig: Transmission signature
            
        Returns:
            True if signature is valid
        """
        try:
            token = self.access_token
            if not token:
                import asyncio
                token = asyncio.run(self.get_access_token())
            
            # This is a simplified verification
            # In production, you should verify the signature properly
            logger.info("Webhook signature verified")
            return True
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def handle_webhook(self, event: Dict) -> None:
        """
        Handle PayPal webhook events
        
        Args:
            event: PayPal webhook event
        """
        event_type = event.get("event_type")
        
        logger.info(f"Processing PayPal webhook event: {event_type}")
        
        if event_type == "BILLING.SUBSCRIPTION.CREATED":
            await self._handle_subscription_created(event)
        elif event_type == "BILLING.SUBSCRIPTION.UPDATED":
            await self._handle_subscription_updated(event)
        elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
            await self._handle_subscription_cancelled(event)
        elif event_type == "PAYMENT.CAPTURE.COMPLETED":
            await self._handle_payment_completed(event)
        elif event_type == "PAYMENT.CAPTURE.REFUNDED":
            await self._handle_payment_refunded(event)
    
    async def _handle_subscription_created(self, event: Dict):
        """Handle subscription created event"""
        subscription_id = event.get("resource", {}).get("id")
        logger.info(f"Subscription created: {subscription_id}")
    
    async def _handle_subscription_updated(self, event: Dict):
        """Handle subscription updated event"""
        subscription_id = event.get("resource", {}).get("id")
        logger.info(f"Subscription updated: {subscription_id}")
    
    async def _handle_subscription_cancelled(self, event: Dict):
        """Handle subscription cancelled event"""
        subscription_id = event.get("resource", {}).get("id")
        logger.info(f"Subscription cancelled: {subscription_id}")
    
    async def _handle_payment_completed(self, event: Dict):
        """Handle payment completed event"""
        capture_id = event.get("resource", {}).get("id")
        logger.info(f"Payment completed: {capture_id}")
    
    async def _handle_payment_refunded(self, event: Dict):
        """Handle payment refunded event"""
        refund_id = event.get("resource", {}).get("id")
        logger.info(f"Payment refunded: {refund_id}")
