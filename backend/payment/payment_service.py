"""
Payment Service
~~~~~~~~~~~~~~~

Unified payment service that handles both Stripe and PayPal.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session

from .models import (
    User, Subscription, Payment, Invoice, UsageRecord, PaymentMethod,
    SubscriptionTier, PaymentStatus, PaymentProvider
)
from .stripe_integration import StripeIntegration
from .paypal_integration import PayPalIntegration

logger = logging.getLogger(__name__)


# Subscription tier pricing
SUBSCRIPTION_PRICING = {
    SubscriptionTier.FREE: {
        "monthly": 0.0,
        "yearly": 0.0,
        "api_calls_limit": 1000,
        "storage_limit_gb": 1.0
    },
    SubscriptionTier.BASIC: {
        "monthly": 29.99,
        "yearly": 299.99,
        "api_calls_limit": 10000,
        "storage_limit_gb": 10.0
    },
    SubscriptionTier.PROFESSIONAL: {
        "monthly": 99.99,
        "yearly": 999.99,
        "api_calls_limit": 100000,
        "storage_limit_gb": 100.0
    },
    SubscriptionTier.ENTERPRISE: {
        "monthly": 499.99,
        "yearly": 4999.99,
        "api_calls_limit": 1000000,
        "storage_limit_gb": 1000.0
    }
}


class PaymentService:
    """
    Unified payment service for PRIV.
    
    Handles all payment and subscription operations across providers.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.stripe = StripeIntegration()
        self.paypal = PayPalIntegration()
    
    async def create_user_with_subscription(
        self,
        email: str,
        full_name: str,
        tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> User:
        """
        Create a new user with a subscription.
        
        Args:
            email: User email
            full_name: User full name
            tier: Subscription tier
            
        Returns:
            Created user
        """
        user_id = str(uuid.uuid4())
        
        user = User(
            user_id=user_id,
            email=email,
            full_name=full_name,
            subscription_tier=tier,
            subscription_status="active",
            subscription_start_date=datetime.utcnow()
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Created user: {user_id} with tier: {tier.value}")
        
        return user
    
    async def upgrade_subscription(
        self,
        user_id: str,
        new_tier: SubscriptionTier,
        provider: PaymentProvider,
        billing_cycle: str = "monthly"
    ) -> Subscription:
        """
        Upgrade user subscription.
        
        Args:
            user_id: User ID
            new_tier: New subscription tier
            provider: Payment provider
            billing_cycle: monthly or yearly
            
        Returns:
            Created subscription
        """
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Get pricing
        pricing = SUBSCRIPTION_PRICING[new_tier]
        price = pricing["monthly"] if billing_cycle == "monthly" else pricing["yearly"]
        
        # Create subscription record
        subscription_id = str(uuid.uuid4())
        subscription = Subscription(
            subscription_id=subscription_id,
            user_id=user_id,
            tier=new_tier,
            status="active",
            price_monthly=pricing["monthly"],
            price_yearly=pricing["yearly"],
            billing_cycle=billing_cycle,
            start_date=datetime.utcnow(),
            next_billing_date=datetime.utcnow() + timedelta(days=30 if billing_cycle == "monthly" else 365),
            provider=provider,
            api_calls_limit=pricing["api_calls_limit"],
            storage_limit_gb=pricing["storage_limit_gb"]
        )
        
        # Create subscription with provider
        if provider == PaymentProvider.STRIPE:
            # Create Stripe customer if needed
            if not user.stripe_customer_id:
                customer = await self.stripe.create_customer(
                    user_id=user_id,
                    email=user.email,
                    name=user.full_name
                )
                user.stripe_customer_id = customer["customer_id"]
            
            # Create Stripe subscription
            # Note: In production, you'd use actual Stripe price IDs
            stripe_price_id = f"price_{new_tier.value}_{billing_cycle}"
            stripe_sub = await self.stripe.create_subscription(
                customer_id=user.stripe_customer_id,
                price_id=stripe_price_id,
                metadata={"subscription_id": subscription_id}
            )
            subscription.provider_subscription_id = stripe_sub["subscription_id"]
        
        elif provider == PaymentProvider.PAYPAL:
            # Create PayPal subscription
            # Note: In production, you'd use actual PayPal plan IDs
            paypal_plan_id = f"plan_{new_tier.value}_{billing_cycle}"
            paypal_sub = await self.paypal.create_subscription(
                plan_id=paypal_plan_id
            )
            subscription.provider_subscription_id = paypal_sub["subscription_id"]
        
        # Update user
        user.subscription_tier = new_tier
        user.subscription_status = "active"
        user.subscription_start_date = datetime.utcnow()
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        
        logger.info(f"Upgraded user {user_id} to {new_tier.value}")
        
        return subscription
    
    async def cancel_subscription(
        self,
        user_id: str,
        at_period_end: bool = True
    ) -> Subscription:
        """
        Cancel user subscription.
        
        Args:
            user_id: User ID
            at_period_end: Cancel at end of billing period
            
        Returns:
            Updated subscription
        """
        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "active"
        ).first()
        
        if not subscription:
            raise ValueError(f"No active subscription found for user: {user_id}")
        
        # Cancel with provider
        if subscription.provider == PaymentProvider.STRIPE:
            await self.stripe.cancel_subscription(
                subscription.provider_subscription_id,
                at_period_end=at_period_end
            )
        elif subscription.provider == PaymentProvider.PAYPAL:
            await self.paypal.cancel_subscription(
                subscription.provider_subscription_id
            )
        
        # Update subscription
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        
        # Update user
        user = self.db.query(User).filter(User.user_id == user_id).first()
        user.subscription_status = "cancelled"
        
        self.db.commit()
        self.db.refresh(subscription)
        
        logger.info(f"Cancelled subscription for user: {user_id}")
        
        return subscription
    
    async def process_payment(
        self,
        user_id: str,
        amount: float,
        currency: str,
        provider: PaymentProvider,
        description: Optional[str] = None
    ) -> Payment:
        """
        Process a one-time payment.
        
        Args:
            user_id: User ID
            amount: Amount to charge
            currency: Currency code
            provider: Payment provider
            description: Payment description
            
        Returns:
            Payment record
        """
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        payment_id = str(uuid.uuid4())
        payment = Payment(
            payment_id=payment_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            provider=provider,
            description=description
        )
        
        try:
            if provider == PaymentProvider.STRIPE:
                # Create Stripe customer if needed
                if not user.stripe_customer_id:
                    customer = await self.stripe.create_customer(
                        user_id=user_id,
                        email=user.email,
                        name=user.full_name
                    )
                    user.stripe_customer_id = customer["customer_id"]
                
                # Create payment intent
                intent = await self.stripe.create_payment_intent(
                    amount=amount,
                    currency=currency,
                    customer_id=user.stripe_customer_id,
                    description=description,
                    metadata={"payment_id": payment_id}
                )
                payment.provider_payment_id = intent["payment_intent_id"]
                payment.provider_customer_id = user.stripe_customer_id
            
            elif provider == PaymentProvider.PAYPAL:
                # Create PayPal order
                order = await self.paypal.create_order(
                    amount=amount,
                    currency=currency,
                    description=description
                )
                payment.provider_payment_id = order["order_id"]
            
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.utcnow()
            
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.failed_at = datetime.utcnow()
            payment.error_message = str(e)
            logger.error(f"Payment failed: {e}")
        
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        return payment
    
    async def track_usage(
        self,
        user_id: str,
        resource_type: str,
        quantity: float,
        unit: str
    ) -> UsageRecord:
        """
        Track resource usage.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            quantity: Quantity used
            unit: Unit of measurement
            
        Returns:
            Usage record
        """
        record_id = str(uuid.uuid4())
        billing_period = datetime.utcnow().strftime("%Y-%m")
        
        record = UsageRecord(
            record_id=record_id,
            user_id=user_id,
            resource_type=resource_type,
            quantity=quantity,
            unit=unit,
            billing_period=billing_period
        )
        
        self.db.add(record)
        
        # Update user usage
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if resource_type == "api_call":
            user.api_calls_this_month += int(quantity)
        elif resource_type == "storage":
            user.storage_used_gb = quantity
        
        self.db.commit()
        self.db.refresh(record)
        
        return record

