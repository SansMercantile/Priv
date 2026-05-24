"""
Payment API Endpoints
REST API for payment and subscription management
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session

from ..database import get_db
from .models import Plan, Subscription, Invoice
from .subscription_manager import SubscriptionManager
from .stripe_service import StripeService
from .paypal_service import PayPalService
from .payfast_service import PayFastService
from .multi_currency_payfast_service import MultiCurrencyPayFastService

logger = logging.getLogger(__name__)

router = APIRouter()
stripe_service = StripeService()
paypal_service = PayPalService()
payfast_service = PayFastService()
multi_currency_payfast = MultiCurrencyPayFastService()


# ============================================================================
# Request/Response Models
# ============================================================================

class PlanResponse(BaseModel):
    """Plan response model"""
    plan_id: str
    name: str
    description: Optional[str]
    price: float
    currency: str
    features: list
    usage_limits: dict
    
    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Subscription response model"""
    subscription_id: str
    user_id: str
    plan_id: str
    status: str
    payment_provider: str
    current_period_start: Optional[str]
    current_period_end: Optional[str]
    cancel_at_period_end: bool
    created_at: Optional[str]
    
    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    """Invoice response model"""
    invoice_id: str
    subscription_id: str
    amount: float
    currency: str
    status: str
    due_date: Optional[str]
    paid_date: Optional[str]
    created_at: Optional[str]
    
    class Config:
        from_attributes = True


class CreateSubscriptionRequest(BaseModel):
    """Create subscription request"""
    plan_id: str
    payment_provider: str  # stripe or paypal
    payment_method_id: Optional[str] = None


class UpdateSubscriptionRequest(BaseModel):
    """Update subscription request"""
    new_plan_id: str


class CancelSubscriptionRequest(BaseModel):
    """Cancel subscription request"""
    at_period_end: bool = False


# ============================================================================
# Plan Endpoints
# ============================================================================

@router.get("/plans", response_model=List[PlanResponse])
async def get_plans(db: Session = Depends(get_db)):
    """
    Get all available plans
    
    Returns:
        List of available plans
    """
    try:
        plans = db.query(Plan).filter(Plan.is_active == True).all()
        return plans
    except Exception as e:
        logger.error(f"Error fetching plans: {e}")
        raise HTTPException(status_code=500, detail="Error fetching plans")


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str, db: Session = Depends(get_db)):
    """
    Get plan details
    
    Args:
        plan_id: Plan ID
        
    Returns:
        Plan details
    """
    try:
        plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching plan: {e}")
        raise HTTPException(status_code=500, detail="Error fetching plan")


# ============================================================================
# Subscription Endpoints
# ============================================================================

@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Create a new subscription
    
    Args:
        request: Create subscription request
        user_id: User ID
        db: Database session
        
    Returns:
        Created subscription
    """
    try:
        manager = SubscriptionManager(db)
        
        # Validate plan exists
        plan = db.query(Plan).filter(Plan.plan_id == request.plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Create subscription with payment provider
        if request.payment_provider == "stripe":
            # Create Stripe customer and subscription
            customer_id = await stripe_service.create_customer(
                user_id=user_id,
                email=f"user_{user_id}@priv.local",
                name=f"User {user_id}"
            )
            
            result = await stripe_service.create_subscription(
                customer_id=customer_id,
                price_id=plan.stripe_price_id or "price_test",
                user_id=user_id
            )
            
            subscription = await manager.create_subscription(
                user_id=user_id,
                plan_id=request.plan_id,
                payment_provider="stripe",
                provider_subscription_id=result["subscription_id"]
            )
        
        elif request.payment_provider == "paypal":
            # Create PayPal subscription
            result = await paypal_service.create_subscription(
                plan_id=plan.paypal_plan_id or "plan_test",
                user_id=user_id,
                email=f"user_{user_id}@priv.local",
                return_url="https://priv.local/subscription/success",
                cancel_url="https://priv.local/subscription/cancel"
            )
            
            subscription = await manager.create_subscription(
                user_id=user_id,
                plan_id=request.plan_id,
                payment_provider="paypal",
                provider_subscription_id=result["subscription_id"]
            )
        
        else:
            raise HTTPException(status_code=400, detail="Invalid payment provider")
        
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    db: Session = Depends(get_db)
):
    """
    Get subscription details
    
    Args:
        subscription_id: Subscription ID
        db: Database session
        
    Returns:
        Subscription details
    """
    try:
        subscription = db.query(Subscription).filter(
            Subscription.subscription_id == subscription_id
        ).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching subscription: {e}")
        raise HTTPException(status_code=500, detail="Error fetching subscription")


@router.get("/subscriptions/user/{user_id}", response_model=Optional[SubscriptionResponse])
async def get_user_subscription(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user's active subscription
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        User's active subscription or None
    """
    try:
        manager = SubscriptionManager(db)
        subscription = await manager.get_user_subscription(user_id)
        return subscription
    except Exception as e:
        logger.error(f"Error fetching user subscription: {e}")
        raise HTTPException(status_code=500, detail="Error fetching subscription")


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    request: CancelSubscriptionRequest,
    db: Session = Depends(get_db)
):
    """
    Cancel a subscription
    
    Args:
        subscription_id: Subscription ID
        request: Cancel request
        db: Database session
        
    Returns:
        Cancellation confirmation
    """
    try:
        manager = SubscriptionManager(db)
        subscription = await manager.get_subscription(subscription_id)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        # Cancel with payment provider
        if subscription.stripe_subscription_id:
            await stripe_service.cancel_subscription(
                subscription.stripe_subscription_id,
                at_period_end=request.at_period_end
            )
        elif subscription.paypal_subscription_id:
            await paypal_service.cancel_subscription(
                subscription.paypal_subscription_id
            )
        
        # Cancel in database
        await manager.cancel_subscription(subscription_id, at_period_end=request.at_period_end)
        
        return {"status": "cancelled", "subscription_id": subscription_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscriptions/{subscription_id}/upgrade")
async def upgrade_subscription(
    subscription_id: str,
    request: UpdateSubscriptionRequest,
    db: Session = Depends(get_db)
):
    """
    Upgrade a subscription
    
    Args:
        subscription_id: Subscription ID
        request: Upgrade request
        db: Database session
        
    Returns:
        Updated subscription
    """
    try:
        manager = SubscriptionManager(db)
        subscription = await manager.get_subscription(subscription_id)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        # Get new plan
        new_plan = db.query(Plan).filter(Plan.plan_id == request.new_plan_id).first()
        if not new_plan:
            raise HTTPException(status_code=404, detail="New plan not found")
        
        # Update with payment provider
        if subscription.stripe_subscription_id:
            await stripe_service.update_subscription(
                subscription.stripe_subscription_id,
                price_id=new_plan.stripe_price_id or "price_test"
            )
        elif subscription.paypal_subscription_id:
            # PayPal doesn't support direct plan changes, would need to cancel and recreate
            pass
        
        # Update in database
        updated = await manager.upgrade_subscription(subscription_id, request.new_plan_id)
        
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Invoice Endpoints
# ============================================================================

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db)
):
    """
    Get invoice details
    
    Args:
        invoice_id: Invoice ID
        db: Database session
        
    Returns:
        Invoice details
    """
    try:
        invoice = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return invoice
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invoice: {e}")
        raise HTTPException(status_code=500, detail="Error fetching invoice")


@router.get("/subscriptions/{subscription_id}/invoices", response_model=List[InvoiceResponse])
async def get_subscription_invoices(
    subscription_id: str,
    db: Session = Depends(get_db)
):
    """
    Get invoices for a subscription
    
    Args:
        subscription_id: Subscription ID
        db: Database session
        
    Returns:
        List of invoices
    """
    try:
        invoices = db.query(Invoice).filter(
            Invoice.subscription_id == subscription_id
        ).all()
        
        return invoices
    except Exception as e:
        logger.error(f"Error fetching invoices: {e}")
        raise HTTPException(status_code=500, detail="Error fetching invoices")


# ============================================================================
# Webhook Endpoints
# ============================================================================

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook
    
    Args:
        request: Request object
        db: Database session
        
    Returns:
        Webhook confirmation
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        event = stripe_service.construct_event(payload, sig_header)
        await stripe_service.handle_webhook(event)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {e}")
        raise HTTPException(status_code=400, detail="Webhook error")


@router.post("/webhooks/paypal")
async def paypal_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle PayPal webhook
    
    Args:
        request: Request object
        db: Database session
        
    Returns:
        Webhook confirmation
    """
    try:
        payload = await request.json()
        await paypal_service.handle_webhook(payload)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing PayPal webhook: {e}")
        raise HTTPException(status_code=400, detail="Webhook error")


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def payment_health():
    """
    Payment system health check
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "stripe": "configured" if stripe_service.api_key else "not configured",
        "paypal": "configured" if paypal_service.client_id else "not configured"
    }

# ============================================================================
# PayFast Endpoints
# ============================================================================

class PayFastPaymentRequest(BaseModel):
       """PayFast payment request model"""
       plan_id: str
       return_url: str
       cancel_url: str
       notify_url: str
       user_email: Optional[str] = None
       user_first_name: Optional[str] = None
       user_last_name: Optional[str] = None

class PayFastSubscriptionRequest(BaseModel):
       """PayFast subscription request model"""
       plan_id: str
       return_url: str
       cancel_url: str
       notify_url: str
       user_email: Optional[str] = None
       user_first_name: Optional[str] = None
       user_last_name: Optional[str] = None
       billing_frequency: Optional[str] = "3"  # 3=monthly, 4=quarterly, 6=annual

@router.post("/payfast/create-payment")
async def create_payfast_payment(
       request: PayFastPaymentRequest,
       user_id: str,
       db: Session = Depends(get_db)
):
       """
       Create a PayFast payment URL for one-time payment
       
       Args:
           request: Payment request data
           user_id: User ID
           db: Database session
           
       Returns:
           Payment URL and details
       """
       try:
           result = payfast_service.create_payment_url(
               db=db,
               user_id=user_id,
               plan_id=request.plan_id,
               return_url=request.return_url,
               cancel_url=request.cancel_url,
               notify_url=request.notify_url,
               user_email=request.user_email,
               user_first_name=request.user_first_name,
               user_last_name=request.user_last_name
           )
           
           if result['success']:
               return result
           else:
               raise HTTPException(status_code=400, detail=result['error'])
               
       except Exception as e:
           logger.error(f"PayFast payment creation error: {str(e)}")
           raise HTTPException(status_code=500, detail=str(e))

@router.post("/payfast/create-subscription")
async def create_payfast_subscription(
       request: PayFastSubscriptionRequest,
       user_id: str,
       db: Session = Depends(get_db)
):
       """
       Create a PayFast subscription
       
       Args:
           request: Subscription request data
           user_id: User ID
           db: Database session
           
       Returns:
           Subscription URL and details
       """
       try:
           result = payfast_service.create_subscription(
               db=db,
               user_id=user_id,
               plan_id=request.plan_id,
               return_url=request.return_url,
               cancel_url=request.cancel_url,
               notify_url=request.notify_url,
               user_email=request.user_email,
               user_first_name=request.user_first_name,
               user_last_name=request.user_last_name,
               billing_frequency=request.billing_frequency
           )
           
           if result['success']:
               return result
           else:
               raise HTTPException(status_code=400, detail=result['error'])
               
       except Exception as e:
           logger.error(f"PayFast subscription creation error: {str(e)}")
           raise HTTPException(status_code=500, detail=str(e))

@router.post("/payfast/itn")
async def payfast_itn_webhook(
       request: Request,
       db: Session = Depends(get_db)
):
       """
       PayFast Instant Transaction Notification (ITN) webhook
       
       Args:
           request: ITN request from PayFast
           db: Database session
           
       Returns:
           ITN processing result
       """
       try:
           # Get form data from ITN
           itn_data = dict(await request.form())
           
           # Process ITN
           result = payfast_service.process_itn_notification(db=db, itn_data=itn_data)
           
           if result['success']:
               return result
           else:
               raise HTTPException(status_code=400, detail=result['error'])
               
       except Exception as e:
           logger.error(f"PayFast ITN processing error: {str(e)}")
           raise HTTPException(status_code=500, detail=str(e))

@router.post("/payfast/cancel-subscription/{subscription_id}")
async def cancel_payfast_subscription(
       subscription_id: str,
       user_id: str,
       db: Session = Depends(get_db)
):
       """
       Cancel a PayFast subscription
       
       Args:
           subscription_id: Subscription ID
           user_id: User ID
           db: Database session
           
       Returns:
           Cancellation result
       """
       try:
           result = payfast_service.cancel_subscription(
               db=db,
               subscription_id=subscription_id,
               user_id=user_id
           )
           
           if result['success']:
               return result
           else:
               raise HTTPException(status_code=400, detail=result['error'])
               
       except Exception as e:
           logger.error(f"PayFast subscription cancellation error: {str(e)}")
           raise HTTPException(status_code=500, detail=str(e))

@router.get("/payfast/subscription/{subscription_id}/status")
async def get_payfast_subscription_status(
       subscription_id: str,
       user_id: str,
       db: Session = Depends(get_db)
):
       """
       Get PayFast subscription status
       
       Args:
           subscription_id: Subscription ID
           user_id: User ID
           db: Database session
           
       Returns:
           Subscription status
       """
       try:
           result = payfast_service.get_subscription_status(
               db=db,
               subscription_id=subscription_id,
               user_id=user_id
           )
           
           if result['success']:
               return result
           else:
               raise HTTPException(status_code=400, detail=result['error'])
               
       except Exception as e:
           logger.error(f"PayFast subscription status error: {str(e)}")
           raise HTTPException(status_code=500, detail=str(e))

@router.get("/payfast/payment-history/{user_id}")
async def get_payfast_payment_history(
       user_id: str,
       limit: int = 50,
       db: Session = Depends(get_db)
):
       """
       Get PayFast payment history for a user
       
       Args:
           user_id: User ID
           limit: Maximum number of records
           db: Database session
           
       Returns:
           Payment history
       """
       try:
           result = payfast_service.get_payment_history(
               db=db,
               user_id=user_id,
               limit=limit
           )
           
           if result['success']:
               return result
           else:
               raise HTTPException(status_code=400, detail=result['error'])
               
       except Exception as e:
           logger.error(f"PayFast payment history error: {str(e)}")
           raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def payment_health():
       """
       Payment system health check
       
       Returns:
           Health status
       """
       return {
           "status": "healthy",
           "stripe": "configured" if stripe_service.api_key else "not configured",
           "paypal": "configured" if paypal_service.client_id else "not configured",
           "payfast": "configured" if payfast_service.merchant_id else "not configured",
           "multi_currency": "enabled",
           "supported_currencies": ["USD", "EUR", "GBP", "CHF", "ZAR", "CAD", "AUD", "JPY"]
       }

# ============================================================================
# Multi-Currency Endpoints
# ============================================================================

class CurrencyDetectionRequest(BaseModel):
       """Request model for currency detection"""
       user_id: str
       country_code: Optional[str] = None
       ip_address: Optional[str] = None
       locale: Optional[str] = None
       preferred_currency: Optional[str] = None
       auto_detect: Optional[bool] = True

class LocalizedPaymentRequest(BaseModel):
       """Request model for localized payment"""
       plan_id: str
       return_url: str
       cancel_url: str
       notify_url: str
       user_email: Optional[str] = None
       user_first_name: Optional[str] = None
       user_last_name: Optional[str] = None
       country_code: Optional[str] = None
       ip_address: Optional[str] = None
       locale: Optional[str] = None

@router.post("/currency/detect")
async def detect_currency(
       request: CurrencyDetectionRequest,
       db: Session = Depends(get_db)
):
       """
       Detect appropriate currency for user based on location and preferences
       
       Args:
           request: Currency detection request
           db: Database session
           
       Returns:
           Detected currency and payment gateway recommendation
       """
       try:
           from shared_resources.backend.multi_currency_billing import get_multi_currency_billing
           
           multi_currency = get_multi_currency_billing()
           
           # Build user data for detection
           user_data = {
               'country_code': request.country_code,
               'ip_address': request.ip_address,
               'locale': request.locale,
               'preferred_currency': request.preferred_currency
           }
           
           # Detect currency
           detected_currency = multi_currency.detect_currency_from_request(user_data)
           
           # Get payment gateway recommendation
           payment_gateway = multi_currency.get_payment_gateway_for_currency(detected_currency)
           
           # Save user preference
           preference = multi_currency_payfast.get_or_create_user_preference(
               db, request.user_id, user_data
           )
           
           return {
               "user_id": request.user_id,
               "detected_currency": detected_currency,
               "currency_info": multi_currency.currency_info[detected_currency].__dict__,
               "recommended_gateway": payment_gateway,
               "user_preference": preference.to_dict(),
               "supported_gateways": {
                   "stripe": ["USD", "EUR", "GBP", "CHF", "CAD", "AUD", "JPY"],
                   "paypal": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"],
                   "payfast": ["ZAR"],
                   "local": ["CNY", "INR", "BRL", "MXN"]
               }
           }
           
       except Exception as e:
           logger.error(f"Currency detection error: {str(e)}")
           raise HTTPException(status_code=500, detail=str(e))

@router.post("/currency/update-preference")
async def update_currency_preference(
       user_id: str,
       currency: str,
       auto_detect: bool = True,
       db: Session = Depends(get_db)
):
       """
       Update user's currency preference
       
       Args:
           user_id: User ID
           currency: Preferred currency code
           auto_detect: Whether to enable auto-detection
           db: Database session
           
       Returns:
           Update result
       """
       try:
           result = multi_currency_payfast.update_user_currency_preference(
               db, user_id, currency, auto_detect
           )
           
           if result['success']:
               return result
           else:
               raise HTTPException(status_code=400, detail=result['error'])
               
       except Exception as e:
           logger.error(f"Currency preference update error: {str(e)}")
           raise HTTPException(status_code=500, detail=str(e))

@router.get("/multi-currency/supported-currencies")
async def get_supported_currencies():
       """
       Get list of supported currencies with information
       
       Returns:
           Supported currencies and their details
       """
       try:
           from shared_resources.backend.multi_currency_billing import get_multi_currency_billing
           
           multi_currency = get_multi_currency_billing()
           
           currencies = {}
           for code, info in multi_currency.currency_info.items():
               currencies[code] = {
                   "code": info.code,
                   "symbol": info.symbol,
                   "name": info.name,
                   "country_codes": info.country_codes,
                   "exchange_rate": info.exchange_rate,
                   "is_primary": info.is_primary,
                   "payment_gateway": info.payment_gateway
               }
           
           return {
               "supported_currencies": currencies,
               "primary_currency": multi_currency.config.get('primary_currency'),
               "gateway_mapping": multi_currency.gateway_mapping,
               "exchange_rates": multi_currency.exchange_rates
           }
           
       except Exception as e:
           logger.error(f"Supported currencies error: {str(e)}")
           raise HTTPException(status_code=500, detail=str(e))
