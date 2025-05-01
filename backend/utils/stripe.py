"""Handles all functionality related to stripe"""

import stripe
from fastapi import APIRouter, Request, Header
from pydantic import BaseModel

from backend.config import settings
from backend.dependencies import DBSession, CurrentAccount
from backend.utils.rate_limiter import limit
from backend.models.shared import Success
from backend.exceptions import *

# Set up Stripe
stripe.api_key = settings.stripe_secret_key

# Models
class CheckoutRequest(BaseModel):
    price_id: str # ID of the Stripe Price object

class CheckoutSession(BaseModel):
    session_id: str

class BillingPortal(BaseModel):
    url: str

# Endpoints

router = APIRouter(prefix="/stripe", tags=["Stripe"])

@router.post("/checkout", response_model=CheckoutSession, status_code=201)
@limit('stripe')
def create_checkout_session(
    request: Request,
    session: DBSession, # type: ignore
    account: CurrentAccount,
    checkout_request: CheckoutRequest,
    mode: str = "subscription",
) -> CheckoutSession:
    """Create a Stripe checkout session"""
    # Create a Stripe customer if they don't have one yet
    if account.customer.stripe_id is None:
        customer = stripe.Customer.create(description=account.username)
        account.customer.stripe_id = customer['id']
        session.add(account)
        session.commit()

    # Create session
    checkout_session = stripe.checkout.Session.create(
        customer=account.customer.stripe_id,
        success_url=settings.app_domain + "/checkout/success?session_id={CHECKOUT_SESSION_ID}", # may change
        cancel_url=settings.app_domain + "/checkout/cancel",
        payment_method_types=["card", "paypal"],
        mode=mode,
        line_items=[{
            "price": checkout_request.price_id,
            "quantity": 1,
        }],
        metadata={ "account_id": account.id }
    )
    return CheckoutSession(session_id=checkout_session['id'])

@router.post("/portal", response_model=BillingPortal, status_code=201)
@limit('account')
def create_billing_portal_session(
    request: Request,
    account: CurrentAccount,
) -> BillingPortal:
    """Creates a Stripe billing portal session"""
    session = stripe.billing_portal.Session.create(
        customer=account.customer.stripe_id,
        return_url=settings.app_domain + "/account", # may change
    )
    return BillingPortal(url=session.url)

@router.post("/webhook", status_code=200, response_model=Success)
# no rate limiting as this is only called by Stripe and must always go through
async def handle_stripe_webhook(
    request: Request,
    session: DBSession, # type: ignore
    stripe_signature: str = Header(str),
) -> Success:
    """Handles the webhook from Stripe"""
    data = await request.body() # can't just use a Pydantic model as request data may vary greatly depending on event
    try:
        event = stripe.Webhook.construct_event( # Make Stripe decode the webhook data
            payload=data,
            sig_header=stripe_signature,
            secret=settings.stripe_webhook_secret,
        )
    except Exception as e:
        raise WebhookError(str(e))
    
    # Handle the event
    # TODO: Maybe do this asynchronously
    type, data = event['type'], event['data']

    # Completed checkout
    if type == 'checkout.session.completed':
        print(type)

    # Subscription renewal
    elif type == 'invoice.paid':
        print(type)

    # Subscription renewal failure
    elif type == 'invoice.payment_failed':
        print(type)

    # Subscription cancellation
    elif type == 'customer.subscription.deleted':
        print(type)

    # Subscription pause
    elif type == 'customer.subscription.paused':
        print(type)

    # Customer deletion (just set customer_id to null, but don't necessarily)
    elif type == 'customer.deleted':
        print(type)

    # Things to possibly handle in the future:
    # - Charge disputes?
    # - Subscription plan updated

    else:
        print(f"Unhandled event: {type}")

    return Success()
