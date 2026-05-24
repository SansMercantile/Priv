"""
PayFast Payment Service
~~~~~~~~~~~~~~~~~~~~~~~

Service layer for PayFast payment operations.
Integrates with the payment models and database.
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session

from .models import (
    Plan, Subscription, Invoice, PaymentMethod, BillingHistory,
    SubscriptionStatus, InvoiceStatus, PaymentProvider
)
from .payfast_integration import PayFastIntegration

logger = logging.getLogger(__name__)


class PayFastService:
    """PayFast payment service implementation."""
    
    def __init__(self, merchant_id: str = None, merchant_key: str = None, 
                 passphrase: str = None, sandbox: bool = True):
        """
        Initialize PayFast service.
        
        Args:
            merchant_id: PayFast merchant ID
            merchant_key: PayFast merchant key
            passphrase: PayFast passphrase
            sandbox: Whether to use sandbox environment
        """
        # Default sandbox credentials (these should be replaced with real credentials in production)
        self.merchant_id = merchant_id or "10000100"
        self.merchant_key = merchant_key or "46f0cd694581a"
        self.passphrase = passphrase or "jt7NOE43FZPn"
        self.sandbox = sandbox
        
        # Initialize PayFast integration
        self.payfast = PayFastIntegration(
            merchant_id=self.merchant_id,
            merchant_key=self.merchant_key,
            passphrase=self.passphrase,
            sandbox=self.sandbox
        )
    
    def create_payment_url(self, db: Session, user_id: str, plan_id: str,
                          return_url: str, cancel_url: str, notify_url: str,
                          user_email: str = None, user_first_name: str = None,
                          user_last_name: str = None) -> Dict[str, Any]:
        """
        Create a payment URL for a one-time payment.
        
        Args:
            db: Database session
            user_id: User ID
            plan_id: Plan ID
            return_url: Success return URL
            cancel_url: Cancel return URL
            notify_url: ITN notification URL
            user_email: User email address
            user_first_name: User first name
            user_last_name: User last name
            
        Returns:
            Dictionary with payment URL and details
        """
        try:
            # Get plan details
            plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
            if not plan:
                raise ValueError(f"Plan {plan_id} not found")
            
            # Create payment data
            payment_data = {
                'amount': plan.price,
                'item_name': plan.name,
                'item_description': plan.description or f"Payment for {plan.name} plan",
                'return_url': return_url,
                'cancel_url': cancel_url,
                'notify_url': notify_url,
                'email_address': user_email or '',
                'name_first': user_first_name or '',
                'name_last': user_last_name or '',
                'custom_str1': user_id,  # Store user_id in custom field
                'custom_str2': plan_id,  # Store plan_id in custom field
            }
            
            # Create payment request
            response = self.payfast.create_payment_request(payment_data)
            
            # Create invoice in database
            invoice = Invoice(
                subscription_id=None,
                amount=plan.price,
                currency=plan.currency,
                status=InvoiceStatus.DRAFT,
                payfast_invoice_token=response['m_payment_id'],
                description=f"One-time payment for {plan.name}",
                user_metadata={'user_id': user_id, 'plan_id': plan_id}
            )
            db.add(invoice)
            db.flush()
            
            # Log billing history
            history = BillingHistory(
                user_id=user_id,
                invoice_id=invoice.invoice_id,
                action='payment_initiated',
                amount=plan.price,
                status='pending',
                details={'provider': 'payfast', 'm_payment_id': response['m_payment_id']}
            )
            db.add(history)
            
            db.commit()
            
            logger.info(f"Created PayFast payment URL for user {user_id}, plan {plan_id}")
            
            return {
                'success': True,
                'payment_url': response['payment_url'],
                'm_payment_id': response['m_payment_id'],
                'invoice_id': invoice.invoice_id,
                'amount': plan.price,
                'currency': plan.currency
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating PayFast payment URL: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_subscription(self, db: Session, user_id: str, plan_id: str,
                           return_url: str, cancel_url: str, notify_url: str,
                           user_email: str = None, user_first_name: str = None,
                           user_last_name: str = None, billing_frequency: str = '3') -> Dict[str, Any]:
        """
        Create a PayFast subscription.
        
        Args:
            db: Database session
            user_id: User ID
            plan_id: Plan ID
            return_url: Success return URL
            cancel_url: Cancel return URL
            notify_url: ITN notification URL
            user_email: User email address
            user_first_name: User first name
            user_last_name: User last name
            billing_frequency: Billing frequency (3=monthly, 4=quarterly, 6=annual)
            
        Returns:
            Dictionary with subscription URL and details
        """
        try:
            # Get plan details
            plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
            if not plan:
                raise ValueError(f"Plan {plan_id} not found")
            
            # Check if user already has an active subscription
            existing_subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            ).first()
            
            if existing_subscription:
                raise ValueError(f"User {user_id} already has an active subscription")
            
            # Create subscription data
            subscription_data = {
                'amount': plan.price,
                'item_name': f"{plan.name} Subscription",
                'item_description': plan.description or f"Monthly subscription to {plan.name} plan",
                'frequency': billing_frequency,
                'cycles': '0',  # Indefinite subscription
                'return_url': return_url,
                'cancel_url': cancel_url,
                'notify_url': notify_url,
                'email_address': user_email or '',
                'name_first': user_first_name or '',
                'name_last': user_last_name or '',
            }
            
            # Create subscription request
            response = self.payfast.create_subscription(subscription_data)
            
            # Create subscription in database
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                status=SubscriptionStatus.PENDING,
                payment_provider=PaymentProvider.PAYFAST,
                payfast_subscription_token=response['token'],
                user_metadata={'billing_frequency': billing_frequency}
            )
            db.add(subscription)
            db.flush()
            
            # Create initial invoice
            invoice = Invoice(
                subscription_id=subscription.subscription_id,
                amount=plan.price,
                currency=plan.currency,
                status=InvoiceStatus.DRAFT,
                payfast_invoice_token=response['token'],
                description=f"Initial payment for {plan.name} subscription",
                user_metadata={'user_id': user_id, 'plan_id': plan_id}
            )
            db.add(invoice)
            db.flush()
            
            # Log billing history
            history = BillingHistory(
                user_id=user_id,
                subscription_id=subscription.subscription_id,
                invoice_id=invoice.invoice_id,
                action='subscription_created',
                amount=plan.price,
                status='pending',
                details={'provider': 'payfast', 'token': response['token']}
            )
            db.add(history)
            
            db.commit()
            
            logger.info(f"Created PayFast subscription for user {user_id}, plan {plan_id}")
            
            return {
                'success': True,
                'subscription_url': response['subscription_url'],
                'subscription_token': response['token'],
                'subscription_id': subscription.subscription_id,
                'amount': plan.price,
                'currency': plan.currency
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating PayFast subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_itn_notification(self, db: Session, itn_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Instant Transaction Notification from PayFast.
        
        Args:
            db: Database session
            itn_data: ITN data received from PayFast
            
        Returns:
            Dictionary with processing result
        """
        try:
            # Verify ITN signature
            if not self.payfast.verify_itn(itn_data):
                raise ValueError("Invalid ITN signature")
            
            # Extract payment details
            payment_status = itn_data.get('payment_status', '')
            m_payment_id = itn_data.get('m_payment_id', '')
            amount_gross = float(itn_data.get('amount_gross', 0))
            user_id = itn_data.get('custom_str1', '')
            plan_id = itn_data.get('custom_str2', '')
            
            logger.info(f"Processing PayFast ITN: {payment_status} for {m_payment_id}")
            
            # Find the invoice
            invoice = db.query(Invoice).filter(
                Invoice.payfast_invoice_token == m_payment_id
            ).first()
            
            if not invoice:
                # Try to find by subscription token
                invoice = db.query(Invoice).filter(
                    Invoice.payfast_invoice_token == m_payment_id
                ).first()
            
            if not invoice:
                raise ValueError(f"Invoice not found for payment ID {m_payment_id}")
            
            # Update invoice based on payment status
            if payment_status == 'COMPLETE':
                invoice.status = InvoiceStatus.PAID
                invoice.paid_date = datetime.utcnow()
                
                # Update subscription if this is a subscription payment
                if invoice.subscription_id:
                    subscription = db.query(Subscription).filter(
                        Subscription.subscription_id == invoice.subscription_id
                    ).first()
                    
                    if subscription and subscription.status == SubscriptionStatus.PENDING:
                        subscription.status = SubscriptionStatus.ACTIVE
                        subscription.current_period_start = datetime.utcnow()
                        # Calculate next billing date based on frequency
                        billing_frequency = subscription.user_metadata.get('billing_frequency', '3')
                        if billing_frequency == '3':  # Monthly
                            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
                        elif billing_frequency == '4':  # Quarterly
                            subscription.current_period_end = datetime.utcnow() + timedelta(days=90)
                        elif billing_frequency == '6':  # Annual
                            subscription.current_period_end = datetime.utcnow() + timedelta(days=365)
                
                # Log billing history
                history = BillingHistory(
                    user_id=user_id or invoice.user_metadata.get('user_id', ''),
                    subscription_id=invoice.subscription_id,
                    invoice_id=invoice.invoice_id,
                    action='payment_completed',
                    amount=amount_gross,
                    status='success',
                    details={'provider': 'payfast', 'itn_data': itn_data}
                )
                db.add(history)
                
            elif payment_status == 'FAILED':
                invoice.status = InvoiceStatus.FAILED
                
                # Log billing history
                history = BillingHistory(
                    user_id=user_id or invoice.user_metadata.get('user_id', ''),
                    subscription_id=invoice.subscription_id,
                    invoice_id=invoice.invoice_id,
                    action='payment_failed',
                    amount=amount_gross,
                    status='failed',
                    details={'provider': 'payfast', 'itn_data': itn_data}
                )
                db.add(history)
            
            db.commit()
            
            logger.info(f"Processed PayFast ITN successfully: {payment_status}")
            
            return {
                'success': True,
                'status': payment_status,
                'message': 'ITN processed successfully'
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing PayFast ITN: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_subscription(self, db: Session, subscription_id: str, user_id: str) -> Dict[str, Any]:
        """
        Cancel a PayFast subscription.
        
        Args:
            db: Database session
            subscription_id: Subscription ID
            user_id: User ID requesting cancellation
            
        Returns:
            Dictionary with cancellation result
        """
        try:
            # Get subscription
            subscription = db.query(Subscription).filter(
                Subscription.subscription_id == subscription_id,
                Subscription.user_id == user_id,
                Subscription.payment_provider == PaymentProvider.PAYFAST
            ).first()
            
            if not subscription:
                raise ValueError(f"PayFast subscription {subscription_id} not found")
            
            if subscription.status != SubscriptionStatus.ACTIVE:
                raise ValueError("Subscription is not active")
            
            # Cancel with PayFast
            success = self.payfast.cancel_subscription(subscription.payfast_subscription_token)
            
            if success:
                # Update local subscription
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.cancelled_at = datetime.utcnow()
                subscription.cancel_at_period_end = True
                
                # Log billing history
                history = BillingHistory(
                    user_id=user_id,
                    subscription_id=subscription_id,
                    action='subscription_cancelled',
                    status='success',
                    details={'provider': 'payfast', 'cancelled_at': datetime.utcnow().isoformat()}
                )
                db.add(history)
                
                db.commit()
                
                logger.info(f"Cancelled PayFast subscription {subscription_id} for user {user_id}")
                
                return {
                    'success': True,
                    'message': 'Subscription cancelled successfully'
                }
            else:
                raise ValueError("Failed to cancel subscription with PayFast")
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error cancelling PayFast subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_subscription_status(self, db: Session, subscription_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get the status of a PayFast subscription.
        
        Args:
            db: Database session
            subscription_id: Subscription ID
            user_id: User ID
            
        Returns:
            Dictionary with subscription status
        """
        try:
            # Get subscription
            subscription = db.query(Subscription).filter(
                Subscription.subscription_id == subscription_id,
                Subscription.user_id == user_id,
                Subscription.payment_provider == PaymentProvider.PAYFAST
            ).first()
            
            if not subscription:
                raise ValueError(f"PayFast subscription {subscription_id} not found")
            
            # Get status from PayFast
            status_data = self.payfast.get_subscription_status(subscription.payfast_subscription_token)
            
            if status_data:
                return {
                    'success': True,
                    'subscription_status': subscription.status.value,
                    'payfast_status': status_data,
                    'current_period_start': subscription.current_period_start.isoformat() if subscription.current_period_start else None,
                    'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                }
            else:
                raise ValueError("Failed to fetch subscription status from PayFast")
                
        except Exception as e:
            logger.error(f"Error getting PayFast subscription status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_history(self, db: Session, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        Get payment history for a user.
        
        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with payment history
        """
        try:
            # Get billing history
            history = db.query(BillingHistory).filter(
                BillingHistory.user_id == user_id
            ).order_by(BillingHistory.created_at.desc()).limit(limit).all()
            
            # Get invoices
            invoices = db.query(Invoice).filter(
                Invoice.payfast_invoice_token.isnot(None)
            ).join(Subscription, Invoice.subscription_id == Subscription.subscription_id).filter(
                Subscription.user_id == user_id
            ).order_by(Invoice.created_at.desc()).limit(limit).all()
            
            return {
                'success': True,
                'billing_history': [h.to_dict() for h in history],
                'invoices': [i.to_dict() for i in invoices]
            }
            
        except Exception as e:
            logger.error(f"Error getting PayFast payment history: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }