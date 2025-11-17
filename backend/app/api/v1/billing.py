"""
Billing & Subscription API Routes
Integrates with Stripe/Paystack/Flutterwave
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from typing import Optional
import stripe

from app.core.config import settings
from app.models.user import User
from app.api.v1.auth import get_current_user

router = APIRouter()

# Initialize Stripe
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSession(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


class CreateSubscription(BaseModel):
    plan_id: str
    payment_method_id: str


@router.post("/checkout-session")
async def create_checkout_session(
    checkout_data: CreateCheckoutSession,
    current_user: User = Depends(get_current_user),
):
    """
    Create Stripe checkout session for subscription
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe not configured",
        )

    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            mode="subscription",
            line_items=[
                {
                    "price": checkout_data.price_id,
                    "quantity": 1,
                }
            ],
            success_url=checkout_data.success_url,
            cancel_url=checkout_data.cancel_url,
        )

        return {"checkout_url": checkout_session.url, "session_id": checkout_session.id}

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhooks for subscription events
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe webhooks not configured",
        )

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle different event types
    event_type = event["type"]

    if event_type == "customer.subscription.created":
        # TODO: Handle subscription created
        pass
    elif event_type == "customer.subscription.updated":
        # TODO: Handle subscription updated
        pass
    elif event_type == "customer.subscription.deleted":
        # TODO: Handle subscription cancelled
        pass
    elif event_type == "invoice.paid":
        # TODO: Handle successful payment
        pass
    elif event_type == "invoice.payment_failed":
        # TODO: Handle failed payment
        pass

    return {"status": "success"}


@router.get("/subscriptions")
async def list_subscriptions(
    current_user: User = Depends(get_current_user),
):
    """List user's subscriptions"""
    # TODO: Implement subscription listing from database
    return {"subscriptions": []}


@router.get("/invoices")
async def list_invoices(
    current_user: User = Depends(get_current_user),
):
    """List user's invoices"""
    # TODO: Implement invoice listing
    return {"invoices": []}
