"""
Multi-Currency PayFast Service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enhanced PayFast service with multi-currency support for global billing.
Handles currency detection, conversion, and localized payment processing.
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session

from .models import (
    Plan, Subscription, Invoice, UserCurrencyPreference, BillingHistory,
    SubscriptionStatus, InvoiceStatus, PaymentProvider
)
from .payfast_integration import PayFastIntegration
from shared_resources.backend.multi_currency_billing import get_multi_currency_billing, Currency

logger = logging.getLogger(__name__)


class MultiCurrencyPayFastService:
    """
    Enhanced PayFast service with multi-currency support.
    
    This service provides global billing capabilities with automatic currency detection,
    conversion, and localization for PayFast payments (primarily ZAR for South Africa).
    """
    
    def __init__(self, merchant_id: str = None, merchant_key: str = None, 
                 passphrase: str = None, sandbox: bool = True):
        """
        Initialize multi-currency PayFast service.
        
        Args:
            merchant_id: PayFast merchant ID
            merchant_key: PayFast merchant key
            passphrase: PayFast passphrase
            sandbox: Whether to use sandbox environment
        """
        # Initialize PayFast integration
        self.payfast = PayFastIntegration(
            merchant_id=merchant_id or "10000100",
            merchant_key=merchant_key or "46f0cd694581a",
            passphrase=passphrase or "jt7NOE43FZPn",
            sandbox=sandbox
        )
        
        # Initialize multi-currency billing
        self.multi_currency = get_multi_currency_billing()
        
        # Default sandbox credentials
        self.merchant_id = merchant_id or "10000100"
        self.merchant_key = merchant_key or "46f0cd694581a"
        self.passphrase = passphrase or "jt7NOE43FZPn"
        self.sandbox = sandbox
    
    def get_or_create_user_preference(self, db: Session, user_id: str, 
                                    user_data: Dict[str, Any] = None) -> UserCurrencyPreference:
        """
        Get or create user currency preference.
        
        Args:
            db: Database session
            user_id: User ID
            user_data: User data for preference detection
            
        Returns:
            UserCurrencyPreference object
        """
        # Try to get existing preference
        preference = db.query(UserCurrencyPreference).filter(
            UserCurrencyPreference.user_id == user_id
        ).first()
        
        if preference:
            # Update preference if new data provided
            if user_data and preference.auto_detect_currency:
                detected_currency = self.multi_currency.detect_currency_from_request(user_data)
                if detected_currency != preference.preferred_currency:
                    preference.preferred_currency = detected_currency
                    preference.updated_at = datetime.utcnow()
                    db.commit()
            
            return preference
        
        # Create new preference
        detected_currency = self.multi_currency.detect_currency_from_request(user_data or {})
        
        preference = UserCurrencyPreference(
            user_id=user_id,
            preferred_currency=detected_currency,
            country_code=user_data.get('country_code') if user_data else None,
            timezone=user_data.get('timezone') if user_data else None,
            locale=user_data.get('locale') if user_data else None,
            auto_detect_currency=True
        )
        
        db.add(preference)
        db.commit()
        
        return preference
    
    def should_use_payfast(self, user_currency: str, user_location: Dict[str, Any]) -> bool:
        """
        Determine if PayFast should be used based on user's currency and location.
        
        Args:
            user_currency: User's preferred currency
            user_location: User's location data
            
        Returns:
            True if PayFast should be used
        """
        # PayFast is primarily for South African customers
        if user_currency == "ZAR":
            return True
        
        # Check if user is in South Africa or neighboring countries
        country_code = user_location.get('country_code', '').upper()
        payfast_countries = ["ZA", "LS", "SZ", "BW", "NA", "ZW", "MW"]
        
        if country_code in payfast_countries:
            return True
        
        # Check if user explicitly prefers PayFast
        if user_location.get('preferred_payment_gateway') == 'payfast':
            return True
        
        return False
    
    def create_localized_payment(self, db: Session, user_id: str, plan_id: str,
                               return_url: str, cancel_url: str, notify_url: str,
                               user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create localized payment URL with currency detection.
        
        Args:
            db: Database session
            user_id: User ID
            plan_id: Plan ID
            return_url: Success return URL
            cancel_url: Cancel return URL
            notify_url: ITN notification URL
            user_data: User information for localization
            
        Returns:
            Dictionary with payment URL and details
        """
        try:
            # Get user preference
            user_preference = self.get_or_create_user_preference(db, user_id, user_data)
            user_currency = user_preference.preferred_currency
            
            # Get plan details
            plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
            if not plan:
                raise ValueError(f"Plan {plan_id} not found")
            
            # Check if PayFast should be used
            if not self.should_use_payfast(user_currency, user_data or {}):
                return {
                    'success': False,
                    'error': f'PayFast not recommended for currency {user_currency}',
                    'suggested_gateway': self.multi_currency.get_payment_gateway_for_currency(user_currency)
                }
            
            # Get localized price in ZAR for PayFast
            zar_price = self.multi_currency.convert_price(
                plan.price, plan.currency, "ZAR"
            )
            
            # Create payment data
            payment_data = {
                'amount': zar_price,
                'item_name': f"{plan.name} ({user_currency} → ZAR)",
                'item_description': f"{plan.description or ''} - Localized pricing for South African market",
                'return_url': return_url,
                'cancel_url': cancel_url,
                'notify_url': notify_url,
                'email_address': user_data.get('email_address', ''),
                'name_first': user_data.get('name_first', ''),
                'name_last': user_data.get('name_last', ''),
                'custom_str1': user_id,
                'custom_str2': plan_id,
                'custom_str3': user_currency,  # Store original currency
                'custom_str4': str(plan.price),  # Store original price
            }
            
            # Create payment request
            response = self.payfast.create_payment_request(payment_data)
            
            # Create invoice with multi-currency info
            invoice = Invoice(
                subscription_id=None,
                amount=zar_price,
                currency="ZAR",
                status=InvoiceStatus.DRAFT,
                payfast_invoice_token=response['m_payment_id'],
                payment_gateway="payfast",
                exchange_rate=self.multi_currency.currency_info["ZAR"].exchange_rate,
                base_amount=plan.price,
                localized_amount=zar_price,
                description=f"One-time payment for {plan.name} (ZAR conversion)",
                user_metadata={
                    'user_id': user_id,
                    'plan_id': plan_id,
                    'original_currency': user_currency,
                    'original_price': plan.price,
                    'conversion_rate': self.multi_currency.currency_info["ZAR"].exchange_rate
                }
            )
            db.add(invoice)
            db.flush()
            
            # Log billing history
            history = BillingHistory(
                user_id=user_id,
                invoice_id=invoice.invoice_id,
                action='payment_initiated',
                amount=zar_price,
                currency="ZAR",
                status='pending',
                details={
                    'provider': 'payfast',
                    'm_payment_id': response['m_payment_id'],
                    'original_currency': user_currency,
                    'original_amount': plan.price,
                    'exchange_rate': self.multi_currency.currency_info["ZAR"].exchange_rate
                }
            )
            db.add(history)
            
            db.commit()
            
            logger.info(f"Created localized PayFast payment for user {user_id}: {plan.currency}{plan.price} → ZAR{zar_price}")
            
            return {
                'success': True,
                'payment_url': response['payment_url'],
                'm_payment_id': response['m_payment_id'],
                'invoice_id': invoice.invoice_id,
                'amount': zar_price,
                'currency': 'ZAR',
                'original_amount': plan.price,
                'original_currency': plan.currency,
                'exchange_rate': self.multi_currency.currency_info["ZAR"].exchange_rate,
                'user_preference': user_preference.to_dict()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating localized PayFast payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_localized_subscription(self, db: Session, user_id: str, plan_id: str,
                                    return_url: str, cancel_url: str, notify_url: str,
                                    user_data: Dict[str, Any] = None,
                                    billing_frequency: str = '3') -> Dict[str, Any]:
        """
        Create localized subscription with currency detection.
        
        Args:
            db: Database session
            user_id: User ID
            plan_id: Plan ID
            return_url: Success return URL
            cancel_url: Cancel return URL
            notify_url: ITN notification URL
            user_data: User information for localization
            billing_frequency: Billing frequency (3=monthly, 4=quarterly, 6=annual)
            
        Returns:
            Dictionary with subscription URL and details
        """
        try:
            # Get user preference
            user_preference = self.get_or_create_user_preference(db, user_id, user_data)
            user_currency = user_preference.preferred_currency
            
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
            
            # Check if PayFast should be used
            if not self.should_use_payfast(user_currency, user_data or {}):
                return {
                    'success': False,
                    'error': f'PayFast not recommended for currency {user_currency}',
                    'suggested_gateway': self.multi_currency.get_payment_gateway_for_currency(user_currency)
                }
            
            # Get localized price in ZAR for PayFast
            zar_price = self.multi_currency.convert_price(
                plan.price, plan.currency, "ZAR"
            )
            
            # Create subscription data
            subscription_data = {
                'amount': zar_price,
                'item_name': f"{plan.name} Subscription ({user_currency} → ZAR)",
                'item_description': f"{plan.description or ''} - Monthly subscription in South African Rand",
                'frequency': billing_frequency,
                'cycles': '0',  # Indefinite subscription
                'return_url': return_url,
                'cancel_url': cancel_url,
                'notify_url': notify_url,
                'email_address': user_data.get('email_address', ''),
                'name_first': user_data.get('name_first', ''),
                'name_last': user_data.get('name_last', ''),
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
                user_metadata={
                    'billing_frequency': billing_frequency,
                    'original_currency': user_currency,
                    'original_price': plan.price,
                    'conversion_rate': self.multi_currency.currency_info["ZAR"].exchange_rate
                }
            )
            db.add(subscription)
            db.flush()
            
            # Create initial invoice
            invoice = Invoice(
                subscription_id=subscription.subscription_id,
                amount=zar_price,
                currency="ZAR",
                status=InvoiceStatus.DRAFT,
                payfast_invoice_token=response['token'],
                payment_gateway="payfast",
                exchange_rate=self.multi_currency.currency_info["ZAR"].exchange_rate,
                base_amount=plan.price,
                localized_amount=zar_price,
                description=f"Initial payment for {plan.name} subscription (ZAR conversion)",
                user_metadata={
                    'user_id': user_id,
                    'plan_id': plan_id,
                    'original_currency': user_currency,
                    'original_price': plan.price,
                    'conversion_rate': self.multi_currency.currency_info["ZAR"].exchange_rate
                }
            )
            db.add(invoice)
            db.flush()
            
            # Log billing history
            history = BillingHistory(
                user_id=user_id,
                subscription_id=subscription.subscription_id,
                invoice_id=invoice.invoice_id,
                action='subscription_created',
                amount=zar_price,
                currency="ZAR",
                status='pending',
                details={
                    'provider': 'payfast',
                    'token': response['token'],
                    'original_currency': user_currency,
                    'original_amount': plan.price,
                    'exchange_rate': self.multi_currency.currency_info["ZAR"].exchange_rate
                }
            )
            db.add(history)
            
            db.commit()
            
            logger.info(f"Created localized PayFast subscription for user {user_id}: {plan.currency}{plan.price} → ZAR{zar_price}")
            
            return {
                'success': True,
                'subscription_url': response['subscription_url'],
                'subscription_token': response['token'],
                'subscription_id': subscription.subscription_id,
                'amount': zar_price,
                'currency': 'ZAR',
                'original_amount': plan.price,
                'original_currency': plan.currency,
                'exchange_rate': self.multi_currency.currency_info["ZAR"].exchange_rate,
                'user_preference': user_preference.to_dict()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating localized PayFast subscription: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_localized_itn(self, db: Session, itn_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process localized ITN notification from PayFast.
        
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
            original_currency = itn_data.get('custom_str3', 'USD')
            original_amount = float(itn_data.get('custom_str4', '0'))
            
            logger.info(f"Processing localized PayFast ITN: {payment_status} for {m_payment_id}")
            
            # Find the invoice
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
                
                # Log billing history with localization info
                history = BillingHistory(
                    user_id=user_id,
                    subscription_id=invoice.subscription_id,
                    invoice_id=invoice.invoice_id,
                    action='payment_completed',
                    amount=amount_gross,
                    currency="ZAR",
                    status='success',
                    details={
                        'provider': 'payfast',
                        'itn_data': itn_data,
                        'original_currency': original_currency,
                        'original_amount': original_amount,
                        'localized_amount': amount_gross,
                        'exchange_rate': invoice.exchange_rate
                    }
                )
                db.add(history)
                
            elif payment_status == 'FAILED':
                invoice.status = InvoiceStatus.FAILED
                
                # Log billing history
                history = BillingHistory(
                    user_id=user_id,
                    subscription_id=invoice.subscription_id,
                    invoice_id=invoice.invoice_id,
                    action='payment_failed',
                    amount=amount_gross,
                    currency="ZAR",
                    status='failed',
                    details={
                        'provider': 'payfast',
                        'itn_data': itn_data,
                        'original_currency': original_currency,
                        'original_amount': original_amount
                    }
                )
                db.add(history)
            
            db.commit()
            
            logger.info(f"Processed localized PayFast ITN successfully: {payment_status}")
            
            return {
                'success': True,
                'status': payment_status,
                'currency': 'ZAR',
                'original_currency': original_currency,
                'message': 'ITN processed successfully'
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing localized PayFast ITN: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_localized_payment_history(self, db: Session, user_id: str, 
                                     preferred_currency: str = None, limit: int = 50) -> Dict[str, Any]:
        """
        Get localized payment history for a user.
        
        Args:
            db: Database session
            user_id: User ID
            preferred_currency: Preferred currency for display
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with localized payment history
        """
        try:
            # Get user preference if no preferred currency specified
            if not preferred_currency:
                user_preference = db.query(UserCurrencyPreference).filter(
                    UserCurrencyPreference.user_id == user_id
                ).first()
                preferred_currency = user_preference.preferred_currency if user_preference else "USD"
            
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
            
            # Localize amounts for display
            localized_history = []
            for h in history:
                localized_amount = h.amount
                localized_currency = h.currency or "USD"
                
                # Convert to preferred currency if different
                if h.currency and h.currency != preferred_currency:
                    try:
                        localized_amount = self.multi_currency.convert_price(
                            h.amount, h.currency, preferred_currency
                        )
                        localized_currency = preferred_currency
                    except Exception as e:
                        logger.warning(f"Failed to convert {h.amount} {h.currency} to {preferred_currency}: {e}")
                
                localized_history.append({
                    **h.to_dict(),
                    'localized_amount': localized_amount,
                    'localized_currency': localized_currency,
                    'formatted_amount': self.multi_currency.get_localized_price(
                        h.amount or 0, preferred_currency
                    )['formatted_amount']
                })
            
            localized_invoices = []
            for invoice in invoices:
                localized_amount = invoice.localized_amount or invoice.amount
                localized_currency = invoice.currency or "USD"
                
                # Convert to preferred currency if different
                if invoice.currency and invoice.currency != preferred_currency:
                    try:
                        # Use base amount for conversion if available
                        base_amount = invoice.base_amount or invoice.amount
                        localized_amount = self.multi_currency.convert_price(
                            base_amount, "USD", preferred_currency
                        )
                        localized_currency = preferred_currency
                    except Exception as e:
                        logger.warning(f"Failed to convert invoice amount: {e}")
                
                localized_invoices.append({
                    **invoice.to_dict(),
                    'localized_amount': localized_amount,
                    'localized_currency': localized_currency,
                    'formatted_amount': self.multi_currency.get_localized_price(
                        invoice.amount or 0, preferred_currency
                    )['formatted_amount']
                })
            
            return {
                'success': True,
                'billing_history': localized_history,
                'invoices': localized_invoices,
                'preferred_currency': preferred_currency,
                'exchange_rates': {
                    currency: info.exchange_rate 
                    for currency, info in self.multi_currency.currency_info.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting localized payment history: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_user_currency_preference(self, db: Session, user_id: str, 
                                       preferred_currency: str, auto_detect: bool = True) -> Dict[str, Any]:
        """
        Update user's currency preference.
        
        Args:
            db: Database session
            user_id: User ID
            preferred_currency: Preferred currency code
            auto_detect: Whether to enable auto-detection
            
        Returns:
            Update result
        """
        try:
            # Validate currency
            if not self.multi_currency.validate_currency_support(preferred_currency):
                raise ValueError(f"Unsupported currency: {preferred_currency}")
            
            # Get or create user preference
            preference = db.query(UserCurrencyPreference).filter(
                UserCurrencyPreference.user_id == user_id
            ).first()
            
            if not preference:
                preference = UserCurrencyPreference(
                    user_id=user_id,
                    preferred_currency=preferred_currency,
                    auto_detect_currency=auto_detect
                )
                db.add(preference)
            else:
                preference.preferred_currency = preferred_currency
                preference.auto_detect_currency = auto_detect
                preference.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Updated currency preference for user {user_id} to {preferred_currency}")
            
            return {
                'success': True,
                'message': f'Currency preference updated to {preferred_currency}',
                'preference': preference.to_dict()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating currency preference: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }