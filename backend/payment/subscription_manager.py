"""
Subscription Manager
Manages subscription lifecycle, billing, and usage tracking
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import (
    Subscription, Plan, Invoice, UsageMetric, PaymentMethod,
    BillingHistory, SubscriptionStatus, InvoiceStatus, PaymentProvider
)

logger = logging.getLogger(__name__)


class SubscriptionManager:
    """Manages subscription operations"""
    
    def __init__(self, db: Session):
        """Initialize subscription manager"""
        self.db = db
    
    async def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        payment_provider: str,
        provider_subscription_id: str,
        metadata: Optional[Dict] = None
    ) -> Subscription:
        """
        Create a new subscription
        
        Args:
            user_id: User ID
            plan_id: Plan ID
            payment_provider: Payment provider (stripe or paypal)
            provider_subscription_id: Provider's subscription ID
            metadata: Additional metadata
            
        Returns:
            Created subscription
        """
        try:
            # Get plan
            plan = self.db.query(Plan).filter(Plan.plan_id == plan_id).first()
            if not plan:
                raise ValueError(f"Plan {plan_id} not found")
            
            # Create subscription
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                status=SubscriptionStatus.ACTIVE,
                payment_provider=PaymentProvider(payment_provider),
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                metadata=metadata or {}
            )
            
            if payment_provider == "stripe":
                subscription.stripe_subscription_id = provider_subscription_id
            elif payment_provider == "paypal":
                subscription.paypal_subscription_id = provider_subscription_id
            
            self.db.add(subscription)
            self.db.commit()
            
            # Log billing history
            await self._log_billing_history(
                user_id=user_id,
                subscription_id=subscription.subscription_id,
                action="created",
                amount=plan.price,
                status="active"
            )
            
            logger.info(f"Created subscription {subscription.subscription_id} for user {user_id}")
            return subscription
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating subscription: {e}")
            raise
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = False
    ) -> Subscription:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Subscription ID
            at_period_end: If True, cancel at end of period
            
        Returns:
            Updated subscription
        """
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.subscription_id == subscription_id
            ).first()
            
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")
            
            if at_period_end:
                subscription.cancel_at_period_end = True
            else:
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.cancelled_at = datetime.utcnow()
            
            subscription.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Log billing history
            await self._log_billing_history(
                user_id=subscription.user_id,
                subscription_id=subscription_id,
                action="cancelled",
                status=subscription.status.value
            )
            
            logger.info(f"Cancelled subscription {subscription_id}")
            return subscription
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling subscription: {e}")
            raise
    
    async def upgrade_subscription(
        self,
        subscription_id: str,
        new_plan_id: str
    ) -> Subscription:
        """
        Upgrade a subscription to a new plan
        
        Args:
            subscription_id: Subscription ID
            new_plan_id: New plan ID
            
        Returns:
            Updated subscription
        """
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.subscription_id == subscription_id
            ).first()
            
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")
            
            # Get new plan
            new_plan = self.db.query(Plan).filter(Plan.plan_id == new_plan_id).first()
            if not new_plan:
                raise ValueError(f"Plan {new_plan_id} not found")
            
            old_plan = subscription.plan
            subscription.plan_id = new_plan_id
            subscription.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Log billing history
            await self._log_billing_history(
                user_id=subscription.user_id,
                subscription_id=subscription_id,
                action="upgraded",
                details={
                    "old_plan": old_plan.name,
                    "new_plan": new_plan.name,
                    "old_price": old_plan.price,
                    "new_price": new_plan.price
                }
            )
            
            logger.info(f"Upgraded subscription {subscription_id} to plan {new_plan_id}")
            return subscription
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error upgrading subscription: {e}")
            raise
    
    async def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """
        Get user's active subscription
        
        Args:
            user_id: User ID
            
        Returns:
            Active subscription or None
        """
        return self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        ).first()
    
    async def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """
        Get subscription by ID
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Subscription or None
        """
        return self.db.query(Subscription).filter(
            Subscription.subscription_id == subscription_id
        ).first()
    
    async def create_invoice(
        self,
        subscription_id: str,
        amount: float,
        description: str = "Monthly subscription",
        due_days: int = 30
    ) -> Invoice:
        """
        Create an invoice
        
        Args:
            subscription_id: Subscription ID
            amount: Invoice amount
            description: Invoice description
            due_days: Days until due
            
        Returns:
            Created invoice
        """
        try:
            invoice = Invoice(
                subscription_id=subscription_id,
                amount=amount,
                description=description,
                due_date=datetime.utcnow() + timedelta(days=due_days),
                status=InvoiceStatus.DRAFT
            )
            self.db.add(invoice)
            self.db.commit()
            
            logger.info(f"Created invoice {invoice.invoice_id} for subscription {subscription_id}")
            return invoice
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating invoice: {e}")
            raise
    
    async def mark_invoice_paid(
        self,
        invoice_id: str,
        paid_date: Optional[datetime] = None
    ) -> Invoice:
        """
        Mark invoice as paid
        
        Args:
            invoice_id: Invoice ID
            paid_date: Payment date
            
        Returns:
            Updated invoice
        """
        try:
            invoice = self.db.query(Invoice).filter(
                Invoice.invoice_id == invoice_id
            ).first()
            
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found")
            
            invoice.status = InvoiceStatus.PAID
            invoice.paid_date = paid_date or datetime.utcnow()
            self.db.commit()
            
            # Log billing history
            await self._log_billing_history(
                user_id=self.db.query(Subscription).filter(
                    Subscription.subscription_id == invoice.subscription_id
                ).first().user_id,
                invoice_id=invoice_id,
                action="paid",
                amount=invoice.amount,
                status="paid"
            )
            
            logger.info(f"Marked invoice {invoice_id} as paid")
            return invoice
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking invoice as paid: {e}")
            raise
    
    async def track_usage(
        self,
        subscription_id: str,
        user_id: str,
        metric_type: str,
        value: float,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> UsageMetric:
        """
        Track usage metric
        
        Args:
            subscription_id: Subscription ID
            user_id: User ID
            metric_type: Type of metric (api_calls, storage, etc.)
            value: Metric value
            period_start: Period start
            period_end: Period end
            
        Returns:
            Created usage metric
        """
        try:
            if not period_start:
                period_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            if not period_end:
                # End of current month
                if period_start.month == 12:
                    period_end = period_start.replace(year=period_start.year + 1, month=1, day=1) - timedelta(seconds=1)
                else:
                    period_end = period_start.replace(month=period_start.month + 1, day=1) - timedelta(seconds=1)
            
            metric = UsageMetric(
                subscription_id=subscription_id,
                user_id=user_id,
                metric_type=metric_type,
                value=value,
                period_start=period_start,
                period_end=period_end
            )
            self.db.add(metric)
            self.db.commit()
            
            logger.info(f"Tracked usage: {metric_type}={value} for user {user_id}")
            return metric
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error tracking usage: {e}")
            raise
    
    async def get_usage_metrics(
        self,
        subscription_id: str,
        metric_type: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> List[UsageMetric]:
        """
        Get usage metrics
        
        Args:
            subscription_id: Subscription ID
            metric_type: Filter by metric type
            period_start: Filter by period start
            period_end: Filter by period end
            
        Returns:
            List of usage metrics
        """
        query = self.db.query(UsageMetric).filter(
            UsageMetric.subscription_id == subscription_id
        )
        
        if metric_type:
            query = query.filter(UsageMetric.metric_type == metric_type)
        
        if period_start:
            query = query.filter(UsageMetric.period_start >= period_start)
        
        if period_end:
            query = query.filter(UsageMetric.period_end <= period_end)
        
        return query.all()
    
    async def _log_billing_history(
        self,
        user_id: str,
        action: str,
        subscription_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        amount: Optional[float] = None,
        status: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> BillingHistory:
        """
        Log billing history
        
        Args:
            user_id: User ID
            action: Action type
            subscription_id: Subscription ID
            invoice_id: Invoice ID
            amount: Amount
            status: Status
            details: Additional details
            
        Returns:
            Created billing history entry
        """
        try:
            history = BillingHistory(
                user_id=user_id,
                subscription_id=subscription_id,
                invoice_id=invoice_id,
                action=action,
                amount=amount,
                status=status,
                details=details or {}
            )
            self.db.add(history)
            self.db.commit()
            return history
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error logging billing history: {e}")
            raise
