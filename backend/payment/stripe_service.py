"""
Stripe Payment Service
Handles all Stripe payment operations including subscriptions, invoices, and webhooks
"""

import stripe
import os
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StripeService:
    """Service for handling Stripe payment operations"""
    
    def __init__(self):
        """Initialize Stripe service with API key"""
        self.api_key = os.getenv("STRIPE_API_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not self.api_key:
            logger.warning("STRIPE_API_KEY not set - Stripe operations will fail")
        
        stripe.api_key = self.api_key
    
    async def create_customer(
        self,
        user_id: str,
        email: str,
        name: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a Stripe customer
        
        Args:
            user_id: User ID
            email: Customer email
            name: Customer name
            metadata: Additional metadata
            
        Returns:
            Stripe customer ID
        """
        try:
            customer_metadata = {"user_id": user_id}
            if metadata:
                customer_metadata.update(metadata)
            
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=customer_metadata
            )
            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {e}")
            raise
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a Stripe subscription
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            user_id: User ID
            metadata: Additional metadata
            
        Returns:
            Subscription details
        """
        try:
            subscription_metadata = {"user_id": user_id}
            if metadata:
                subscription_metadata.update(metadata)
            
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
                metadata=subscription_metadata
            )
            
            logger.info(f"Created Stripe subscription {subscription.id} for user {user_id}")
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe subscription: {e}")
            raise
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = False
    ) -> Dict:
        """
        Cancel a Stripe subscription
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of period; if False, cancel immediately
            
        Returns:
            Subscription details
        """
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
            
            logger.info(f"Cancelled Stripe subscription {subscription_id}")
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "canceled_at": subscription.canceled_at
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling Stripe subscription: {e}")
            raise
    
    async def update_subscription(
        self,
        subscription_id: str,
        price_id: str
    ) -> Dict:
        """
        Update a Stripe subscription (upgrade/downgrade)
        
        Args:
            subscription_id: Stripe subscription ID
            price_id: New Stripe price ID
            
        Returns:
            Updated subscription details
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            updated = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription.items.data[0].id,
                    "price": price_id
                }],
                proration_behavior="create_prorations"
            )
            
            logger.info(f"Updated Stripe subscription {subscription_id}")
            
            return {
                "subscription_id": updated.id,
                "status": updated.status,
                "current_period_end": updated.current_period_end
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error updating Stripe subscription: {e}")
            raise
    
    async def get_subscription(self, subscription_id: str) -> Dict:
        """
        Get subscription details
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Subscription details
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "items": [item.price.id for item in subscription.items.data]
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving Stripe subscription: {e}")
            raise
    
    async def get_invoice(self, invoice_id: str) -> Dict:
        """
        Get invoice details
        
        Args:
            invoice_id: Stripe invoice ID
            
        Returns:
            Invoice details
        """
        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            return {
                "invoice_id": invoice.id,
                "amount": invoice.amount_paid,
                "status": invoice.status,
                "paid_at": invoice.paid_at,
                "pdf_url": invoice.invoice_pdf,
                "number": invoice.number
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving Stripe invoice: {e}")
            raise
    
    async def list_invoices(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        List invoices for a customer
        
        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return
            
        Returns:
            List of invoice details
        """
        try:
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )
            return [
                {
                    "invoice_id": inv.id,
                    "amount": inv.amount_paid,
                    "status": inv.status,
                    "paid_at": inv.paid_at,
                    "created": inv.created
                }
                for inv in invoices.data
            ]
        except stripe.error.StripeError as e:
            logger.error(f"Error listing Stripe invoices: {e}")
            raise
    
    def construct_event(self, payload: bytes, sig_header: str) -> Dict:
        """
        Construct and verify Stripe webhook event
        
        Args:
            payload: Webhook payload
            sig_header: Stripe signature header
            
        Returns:
            Verified event
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                self.webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise
    
    async def handle_webhook(self, event: Dict) -> None:
        """
        Handle Stripe webhook events
        
        Args:
            event: Stripe webhook event
        """
        event_type = event.get("type")
        
        logger.info(f"Processing Stripe webhook event: {event_type}")
        
        if event_type == "customer.subscription.updated":
            await self._handle_subscription_updated(event["data"]["object"])
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_deleted(event["data"]["object"])
        elif event_type == "invoice.payment_succeeded":
            await self._handle_invoice_paid(event["data"]["object"])
        elif event_type == "invoice.payment_failed":
            await self._handle_invoice_failed(event["data"]["object"])
        elif event_type == "charge.refunded":
            await self._handle_charge_refunded(event["data"]["object"])
    
    async def _handle_subscription_updated(self, subscription: Dict):
        """Handle subscription update event"""
        logger.info(f"Subscription updated: {subscription['id']}")
        # Update database with new subscription status
        # This will be implemented in the subscription manager
    
    async def _handle_subscription_deleted(self, subscription: Dict):
        """Handle subscription cancellation event"""
        logger.info(f"Subscription deleted: {subscription['id']}")
        # Update database to mark subscription as cancelled
    
    async def _handle_invoice_paid(self, invoice: Dict):
        """Handle invoice payment success event"""
        logger.info(f"Invoice paid: {invoice['id']}")
        # Update database to mark invoice as paid
    
    async def _handle_invoice_failed(self, invoice: Dict):
        """Handle invoice payment failure event"""
        logger.error(f"Invoice payment failed: {invoice['id']}")
        # Update database to mark invoice as failed
        # Send notification to user
    
    async def _handle_charge_refunded(self, charge: Dict):
        """Handle charge refund event"""
        logger.info(f"Charge refunded: {charge['id']}")
        # Update database to mark invoice as refunded
