"""
Stripe Payment Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Handles all Stripe payment processing and subscription management.
"""

import os
import logging
from typing import Dict, Optional, Any
import stripe
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_placeholder")


class StripeIntegration:
    """
    Stripe payment integration for PRIV.
    
    Handles:
    - Customer creation
    - Payment processing
    - Subscription management
    - Webhook handling
    """
    
    def __init__(self):
        self.api_key = stripe.api_key
    
    async def create_customer(
        self,
        user_id: str,
        email: str,
        name: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe customer.
        
        Args:
            user_id: Internal user ID
            email: Customer email
            name: Customer name
            metadata: Additional metadata
            
        Returns:
            Stripe customer object
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "user_id": user_id,
                    **(metadata or {})
                }
            )
            
            logger.info(f"Created Stripe customer: {customer.id} for user: {user_id}")
            
            return {
                "customer_id": customer.id,
                "email": customer.email,
                "name": customer.name,
                "created": customer.created
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            raise
    
    async def create_payment_intent(
        self,
        amount: float,
        currency: str,
        customer_id: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a payment intent.
        
        Args:
            amount: Amount in dollars
            currency: Currency code (USD, EUR, etc.)
            customer_id: Stripe customer ID
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            Payment intent object
        """
        try:
            # Convert dollars to cents
            amount_cents = int(amount * 100)
            
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                customer=customer_id,
                description=description,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True}
            )
            
            logger.info(f"Created payment intent: {payment_intent.id} for ${amount}")
            
            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": amount,
                "currency": currency,
                "status": payment_intent.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Payment intent creation failed: {e}")
            raise
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            trial_days: Number of trial days
            metadata: Additional metadata
            
        Returns:
            Subscription object
        """
        try:
            subscription_params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": metadata or {}
            }
            
            if trial_days:
                subscription_params["trial_period_days"] = trial_days
            
            subscription = stripe.Subscription.create(**subscription_params)
            
            logger.info(f"Created subscription: {subscription.id} for customer: {customer_id}")
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "trial_end": datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Subscription creation failed: {e}")
            raise
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: Cancel at end of billing period
            
        Returns:
            Updated subscription object
        """
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
            
            logger.info(f"Cancelled subscription: {subscription_id}")
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "cancelled_at": datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Subscription cancellation failed: {e}")
            raise
    
    async def update_subscription(
        self,
        subscription_id: str,
        new_price_id: str
    ) -> Dict[str, Any]:
        """
        Update subscription to a new price/tier.
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New Stripe price ID
            
        Returns:
            Updated subscription object
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": new_price_id
                }],
                proration_behavior="create_prorations"
            )
            
            logger.info(f"Updated subscription: {subscription_id} to price: {new_price_id}")
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end)
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Subscription update failed: {e}")
            raise
    
    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        mode: str = "subscription"
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session.
        
        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            mode: payment or subscription
            
        Returns:
            Checkout session object
        """
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                line_items=[{"price": price_id, "quantity": 1}],
                mode=mode,
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            logger.info(f"Created checkout session: {session.id}")
            
            return {
                "session_id": session.id,
                "url": session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Checkout session creation failed: {e}")
            raise
    
    async def get_payment_status(
        self,
        payment_intent_id: str
    ) -> Dict[str, Any]:
        """
        Get payment intent status.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            Payment status information
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "payment_intent_id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_intent.amount / 100,
                "currency": payment_intent.currency.upper()
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Payment status retrieval failed: {e}")
            raise
    
    async def get_subscription_status(
        self,
        subscription_id: str
    ) -> Dict[str, Any]:
        """
        Get subscription status.
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Subscription status information
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Subscription status retrieval failed: {e}")
            raise

