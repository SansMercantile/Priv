"""
PRIV Payment System Models
Database models for payment processing, subscriptions, and billing
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
import uuid

Base = declarative_base(metadata=None)


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enumeration"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    EXPIRED = "expired"
    PENDING = "pending"


class InvoiceStatus(str, enum.Enum):
    """Invoice status enumeration"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    OVERDUE = "overdue"


class PaymentProvider(str, enum.Enum):
    """Payment provider enumeration"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    PAYFAST = "payfast"


class Plan(Base):
    """Subscription plan model"""
    __tablename__ = "plans"
    
    plan_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)  # Free, Pro, Enterprise
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)  # Monthly price in USD
    currency = Column(String, default="USD")
    features = Column(JSON, nullable=False)  # List of features
    usage_limits = Column(JSON, nullable=False)  # Usage limits
    stripe_price_id = Column(String, nullable=True)
    paypal_plan_id = Column(String, nullable=True)
    payfast_plan_token = Column(String, nullable=True)
    # Multi-currency support
    localized_prices = Column(JSON, nullable=True)  # Dictionary of currency: price
    supported_currencies = Column(JSON, nullable=False, default=lambda: ["USD"])
    pricing_model = Column(String, default="fixed")  # fixed, dynamic, tiered
    geo_pricing_enabled = Column(Boolean, default=False)
    base_currency = Column(String, default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subscriptions = relationship("Subscription", back_populates="plan")
    
    def to_dict(self):
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "currency": self.currency,
            "features": self.features,
            "usage_limits": self.usage_limits,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Subscription(Base):
    """User subscription model"""
    __tablename__ = "subscriptions"
    
    subscription_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    plan_id = Column(String, ForeignKey("plans.plan_id"), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING)
    payment_provider = Column(Enum(PaymentProvider), nullable=False)
    stripe_subscription_id = Column(String, nullable=True, unique=True)
    paypal_subscription_id = Column(String, nullable=True, unique=True)
    payfast_subscription_token = Column(String, nullable=True, unique=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    user_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    plan = relationship("Plan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")
    usage_metrics = relationship("UsageMetric", back_populates="subscription")
    
    def to_dict(self):
        return {
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "plan_id": self.plan_id,
            "status": self.status.value if self.status else None,
            "payment_provider": self.payment_provider.value if self.payment_provider else None,
            "current_period_start": self.current_period_start.isoformat() if self.current_period_start else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "cancel_at_period_end": self.cancel_at_period_end,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Invoice(Base):
    """Invoice model"""
    __tablename__ = "invoices"
    
    invoice_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String, ForeignKey("subscriptions.subscription_id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    stripe_invoice_id = Column(String, nullable=True, unique=True)
    paypal_invoice_id = Column(String, nullable=True, unique=True)
    payfast_invoice_token = Column(String, nullable=True, unique=True)
    due_date = Column(DateTime, nullable=True)
    paid_date = Column(DateTime, nullable=True)
    description = Column(String, nullable=True)
    line_items = Column(JSON, nullable=True)
    user_metadata = Column(JSON, nullable=True)
    # Multi-currency support
    exchange_rate = Column(Float, nullable=True)  # Exchange rate at time of invoicing
    base_amount = Column(Float, nullable=True)  # Amount in base currency (USD)
    localized_amount = Column(Float, nullable=True)  # Amount in local currency
    payment_gateway = Column(String, default="stripe")  # stripe, paypal, payfast, local
    tax_info = Column(JSON, nullable=True)  # Tax information by jurisdiction
    discount_info = Column(JSON, nullable=True)  # Regional discounts
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subscription = relationship("Subscription", back_populates="invoices")
    
    def to_dict(self):
        return {
            "invoice_id": self.invoice_id,
            "subscription_id": self.subscription_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value if self.status else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "paid_date": self.paid_date.isoformat() if self.paid_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UsageMetric(Base):
    """Usage metrics for billing"""
    __tablename__ = "usage_metrics"
    
    metric_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String, ForeignKey("subscriptions.subscription_id"), nullable=False)
    user_id = Column(String, nullable=False, index=True)
    metric_type = Column(String, nullable=False)  # api_calls, storage, concurrent_connections, etc.
    value = Column(Float, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    subscription = relationship("Subscription", back_populates="usage_metrics")
    
    def to_dict(self):
        return {
            "metric_id": self.metric_id,
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "metric_type": self.metric_type,
            "value": self.value,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }


class PaymentMethod(Base):
    """Payment method storage"""
    __tablename__ = "payment_methods"
    
    payment_method_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    payment_provider = Column(Enum(PaymentProvider), nullable=False)
    provider_payment_method_id = Column(String, nullable=False)
    card_last_four = Column(String, nullable=True)
    card_brand = Column(String, nullable=True)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "payment_method_id": self.payment_method_id,
            "user_id": self.user_id,
            "payment_provider": self.payment_provider.value if self.payment_provider else None,
            "card_last_four": self.card_last_four,
            "card_brand": self.card_brand,
            "is_default": self.is_default,
            "is_active": self.is_active,
        }


class UserCurrencyPreference(Base):
    """User currency preferences and localization settings"""
    __tablename__ = "user_currency_preferences"
    
    preference_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True, unique=True)
    preferred_currency = Column(String, default="USD")
    country_code = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    locale = Column(String, nullable=True)
    auto_detect_currency = Column(Boolean, default=True)
    payment_method_preferences = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "preference_id": self.preference_id,
            "user_id": self.user_id,
            "preferred_currency": self.preferred_currency,
            "country_code": self.country_code,
            "timezone": self.timezone,
            "locale": self.locale,
            "auto_detect_currency": self.auto_detect_currency,
            "payment_method_preferences": self.payment_method_preferences,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BillingHistory(Base):
    """Billing history for audit trail"""
    __tablename__ = "billing_history"
    
    history_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    subscription_id = Column(String, nullable=True)
    invoice_id = Column(String, nullable=True)
    action = Column(String, nullable=False)  # created, updated, paid, failed, refunded, etc.
    amount = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    status = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "history_id": self.history_id,
            "user_id": self.user_id,
            "subscription_id": self.subscription_id,
            "invoice_id": self.invoice_id,
            "action": self.action,
            "amount": self.amount,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
