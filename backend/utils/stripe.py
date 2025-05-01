"""Handles all functionality related to stripe"""

import stripe
from fastapi import APIRouter, Request, Header
from pydantic import BaseModel
from datetime import datetime, UTC

from backend.config import settings
from backend.dependencies import DBSession, CurrentAccount
from backend.database.schema import DBCustomer
from backend.database import accounts as accounts_db
from backend.utils.rate_limiter import limit
from backend.models.shared import Success
from backend.exceptions import *

# Set up Stripe
stripe.api_key = settings.stripe_secret_key

# Models
class CheckoutRequest(BaseModel):
    price_id: str # ID of the Stripe Price object

class CheckoutSession(BaseModel):
    url: str

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
    return CheckoutSession(url=checkout_session['url'])

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
    # TODO: Maybe do this asynchronously so we can return the 200 more quickly, but none of this should take long
    type, data = event['type'], event['data']['object']

    # Subscription renewal
    if type == 'invoice.paid':
        # Extract relevant info
        customer_id = data['customer']
        purchase = data['lines']['data'][0]
        key, exp = purchase['price']['lookup_key'], purchase['period']['end']
        exp = datetime.fromtimestamp(exp).astimezone(UTC)

        # Update the customer in the database
        customer: DBCustomer = accounts_db.get_by_stripe_id(session, customer_id)
        customer.type = "active"
        customer.expiration = exp
        session.add(customer)
        session.commit()

        # TODO: Send confirmation email

    # Subscription renewal failure
    elif type == 'invoice.payment_failed':
        # Extract relevant info
        customer_id = data['customer']

        # Update the customer in the database. Mark them as inactive.
        customer: DBCustomer = accounts_db.get_by_stripe_id(session, customer_id)
        customer.type = "inactive" if customer.type == "active" else customer.type
        session.add(customer)
        session.commit()

        # TODO: Send the customer an email letting them know of the failure.

    # Subscription cancellation
    elif type == 'customer.subscription.deleted':
        # Extract relevant info
        customer_id = data['customer']

        # Update the customer in the database. Mark it as terminated.
        customer: DBCustomer = accounts_db.get_by_stripe_id(session, customer_id)
        customer.type = "terminated" if customer.type == "active" else customer.type
        session.add(customer)
        session.commit()

        # TODO: Send a "Sorry to see you go!" email as confirmation.

    # Subscription pause
    elif type == 'customer.subscription.paused':
        # Extract relevant info
        customer_id = data['customer']

        # Update the customer in the database. Mark it as terminated.
        customer: DBCustomer = accounts_db.get_by_stripe_id(session, customer_id)
        customer.type = "terminated" if customer.type == "active" else customer.type
        session.add(customer)
        session.commit()

        # TODO: Send confirmation email

    # Customer deletion (just set customer_id to null, but don't necessarily revoke permissions)
    elif type == 'customer.deleted':
        # Extract relevant info
        customer_id = data['id']

        # Update the customer in the database. If they have an active subscription, mark it as terminated.
        try:
            customer: DBCustomer = accounts_db.get_by_stripe_id(session, customer_id)
            customer.type = "terminated" if customer.type == "active" else customer.type
            customer.stripe_id = None
            session.add(customer)
            session.commit()
        except EntityNotFound as e: # If this was triggered by an account deletion, do nothing
            pass

    # Things to possibly handle in the future:
    # - Charge disputes?
    # - Subscription plan updated

    else:
        print(f"Unhandled event: {type}")

    return Success()

# Non-route function to delete a customer. For when a user deletes their account.
def delete_customer(
    customer: DBCustomer,
) -> None:
    """Delete a Stripe customer"""
    if customer.stripe_id is not None:
        stripe.Customer.delete(customer.stripe_id)