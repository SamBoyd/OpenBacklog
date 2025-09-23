# Stripe webhook handler for the event:checkout.session.completed
import logging
import uuid
from http.client import HTTPException
from typing import List, Optional

import stripe
from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.accounting import accounting_controller
from src.accounting.billing_service import BillingService
from src.accounting.billing_state_machine import AccountStatusResponse
from src.accounting.models import PendingTopup, PendingTopupStatus, UserAccountDetails
from src.accounting.stripe_service import StripeService
from src.config import settings
from src.db import get_db
from src.main import app
from src.models import User
from src.views import dependency_to_override

logger = logging.getLogger(__name__)

stripe.api_key = settings.stripe_secret_key


@app.post("/api/stripe/webhook", response_class=JSONResponse)
async def stripe_webhook_handler(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook events for checkout sessions.

    This endpoint processes Stripe webhook events and delegates billing operations
    to the StripeService for proper business logic handling.

    Supported events:
    - checkout.session.completed: Payment succeeded immediately
    - checkout.session.expired: Session expired without payment
    - checkout.session.async_payment_failed: Payment failed asynchronously
    - checkout.session.async_payment_succeeded: Payment succeeded asynchronously
    """
    body = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        logger.error("No Stripe signature provided in webhook")
        raise HTTPException(status_code=400, detail="No signature provided")

    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            body, signature, settings.stripe_webhook_secret
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    logger.info(f"Processing Stripe webhook event: {event['type']}")

    # Handle the event based on type
    stripe_service = StripeService(db)

    if event["type"] == "checkout.session.completed":
        stripe_service.handle_checkout_session_completed(event)
    elif event["type"] == "checkout.session.expired":
        stripe_service.handle_checkout_session_expired(event)
    elif event["type"] == "checkout.session.async_payment_failed":
        stripe_service.handle_checkout_session_async_payment_failed(event)
    elif event["type"] == "checkout.session.async_payment_succeeded":
        stripe_service.handle_checkout_session_async_payment_succeeded(event)
    elif event["type"] == "customer.subscription.created":
        accounting_controller.handle_subscription_created_with_setup(event, db)
    elif event["type"] == "customer.subscription.updated":
        stripe_service.handle_subscription_updated(event)
    elif event["type"] == "customer.subscription.deleted":
        stripe_service.handle_subscription_deleted_through_stripe_portal(event)
    elif event["type"] == "setup_intent.succeeded":
        stripe_service.handle_setup_intent_succeeded(event)
    else:
        logger.info(f"Unhandled event type: {event['type']}")

    return JSONResponse(content={"received": True}, status_code=200)


class TopupRequest(BaseModel):
    amount_cents: int


class TopupResponse(BaseModel):
    ok: bool
    redirect_url: str


class PaymentMethodData(BaseModel):
    """Stripe payment method data."""

    id: str
    type: str
    card_brand: Optional[str] = Field(
        description="Card brand", alias="cardBrand", default=None
    )
    card_last4: Optional[str] = Field(
        description="Card last 4 digits", alias="cardLast4", default=None
    )
    card_exp_month: Optional[int] = Field(
        description="Card expiration month", alias="cardExpMonth", default=None
    )
    card_exp_year: Optional[int] = Field(
        description="Card expiration year", alias="cardExpYear", default=None
    )
    is_default: bool = Field(
        description="Whether this is the default payment method",
        alias="isDefault",
        default=False,
    )


class PaymentMethodsResponse(BaseModel):
    """Response model for payment methods."""

    payment_methods: List[PaymentMethodData] = Field(
        description="List of payment methods",
        alias="paymentMethods",
        default_factory=list,
    )
    default_payment_method_id: Optional[str] = Field(
        description="Default payment method ID",
        alias="defaultPaymentMethodId",
        default=None,
    )


class CustomerPortalSessionResponse(BaseModel):
    """Response model for customer portal session."""

    url: str = Field(description="Customer portal session URL")


class BillingDetailsData(BaseModel):
    """Response model for billing details."""

    email: Optional[str] = Field(description="Customer email address", default=None)
    name: Optional[str] = Field(description="Customer name", default=None)
    phone: Optional[str] = Field(description="Customer phone number", default=None)
    address_line1: Optional[str] = Field(
        description="Address line 1", alias="addressLine1", default=None
    )
    address_line2: Optional[str] = Field(
        description="Address line 2", alias="addressLine2", default=None
    )
    address_city: Optional[str] = Field(
        description="City", alias="addressCity", default=None
    )
    address_state: Optional[str] = Field(
        description="State", alias="addressState", default=None
    )
    address_postal_code: Optional[str] = Field(
        description="Postal code", alias="addressPostalCode", default=None
    )
    address_country: Optional[str] = Field(
        description="Country", alias="addressCountry", default=None
    )
    tax_id: Optional[str] = Field(description="Tax ID", alias="taxId", default=None)


class BillingDetailsResponse(BaseModel):
    """Response model for billing details."""

    billing_details: BillingDetailsData = Field(
        description="Customer billing details", alias="billingDetails"
    )


class SubscriptionCheckoutRequest(BaseModel):
    """Request model for subscription checkout."""

    payment_method_id: Optional[str] = Field(
        default=None, description="Payment method ID for manual card payment"
    )
    express_checkout: bool = Field(
        default=False, description="Whether this is an express checkout flow"
    )


class SubscriptionCheckoutResponse(BaseModel):
    """Response model for subscription checkout."""

    client_secret: str = Field(
        description="Setup intent client secret for frontend confirmation"
    )


@app.post("/api/billing/topup", response_class=JSONResponse)
def topup_account(
    request: TopupRequest,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
):
    logger.info(f"Topup request received: {request}")

    if not user.account_details.stripe_customer_id:
        raise Exception("User account not onboarded")

    try:
        # Create a pending topup record first
        billing_service = BillingService(db)
        pending_topup = billing_service.create_pending_topup(
            user_id=user.id,
            session_id=f"pending_{uuid.uuid4()}",
            amount_cents=request.amount_cents,
        )

        checkout_session = stripe.checkout.Session.create(
            customer=user.account_details.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Account Topup",
                            "description": f"Topup account with ${request.amount_cents / 100:.2f}",
                        },
                        "unit_amount": request.amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{settings.app_url}/api/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.app_url}/api/billing/cancel?session_id={{CHECKOUT_SESSION_ID}}",
            metadata={
                "user_id": str(user.id),
                "topup_amount_cents": str(request.amount_cents),
                "type": "account_topup",
            },
            invoice_creation={
                "enabled": True,
                "invoice_data": {
                    "description": f"Account topup for ${request.amount_cents / 100:.2f}",
                    "metadata": {
                        "user_id": str(user.id),
                        "topup_amount_cents": str(request.amount_cents),
                        "type": "account_topup",
                    },
                },
            },
        )

        # Update the pending topup with the actual session ID
        pending_topup.session_id = checkout_session.id
        db.add(pending_topup)
        db.commit()

        logger.info(
            f"Created checkout session {checkout_session.id} for user {user.id}"
        )

        return JSONResponse(
            content={"ok": True, "redirect_url": checkout_session.url}, status_code=200
        )

    except stripe.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {e}")
        raise Exception(f"Failed to create checkout session: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating checkout session: {e}")
        raise Exception(f"Failed to create checkout session: {str(e)}")


@app.get("/api/billing/success")
def billing_success(
    request: Request,
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
):
    """
    Handle successful topup payment completion.

    This endpoint is called when a user successfully completes a topup payment.
    It verifies the session exists and checks payment status, then redirects appropriately.
    The actual payment processing happens in the Stripe webhook.
    """
    session_id = request.query_params.get("session_id")
    if not session_id:
        logger.error("No session_id provided in success URL")
        return RedirectResponse(
            url=f"{settings.app_url}/workspace/billing?error=no_session"
        )

    try:
        # Retrieve the checkout session from Stripe to verify it exists
        checkout_session = stripe.checkout.Session.retrieve(session_id)

        # Verify the session belongs to the current user
        session_metadata = checkout_session.metadata or {}
        if session_metadata.get("user_id") != str(user.id):
            logger.error(f"Session {session_id} does not belong to user {user.id}")
            return RedirectResponse(
                url=f"{settings.app_url}/workspace/billing?error=unauthorized"
            )

        # Check if we have a pending topup for this session
        pending_topup = (
            db.query(PendingTopup).filter(PendingTopup.session_id == session_id).first()
        )

        if not pending_topup:
            logger.warning(f"No pending topup found for session {session_id}")
            return RedirectResponse(
                url=f"{settings.app_url}/workspace/billing?error=no_pending_topup"
            )

        # Check the payment status to provide appropriate feedback
        payment_status = checkout_session.payment_status
        if payment_status == "paid":
            logger.info(
                f"User {user.id} completed checkout for session {session_id} with immediate payment. "
                f"Payment will be processed via webhook."
            )
            return RedirectResponse(
                url=f"{settings.app_url}/workspace/billing?pending=payment_processing"
            )
        elif payment_status == "pending":
            logger.info(
                f"User {user.id} completed checkout for session {session_id} with pending payment. "
                f"Payment will be processed when confirmed via webhook."
            )
            return RedirectResponse(
                url=f"{settings.app_url}/workspace/billing?pending=payment_pending"
            )
        else:
            logger.warning(
                f"User {user.id} completed checkout for session {session_id} with payment status: {payment_status}"
            )
            return RedirectResponse(
                url=f"{settings.app_url}/workspace/billing?error=payment_status_unknown"
            )

    except stripe.StripeError as e:
        logger.error(f"Stripe error retrieving session {session_id}: {e}")
        return RedirectResponse(
            url=f"{settings.app_url}/workspace/billing?error=stripe_error"
        )
    except Exception as e:
        logger.error(f"Unexpected error processing topup success: {e}")
        return RedirectResponse(
            url=f"{settings.app_url}/workspace/billing?error=processing_error"
        )


@app.get("/api/billing/cancel")
def billing_cancel(
    request: Request,
    user=Depends(dependency_to_override),
    db: Session = Depends(get_db),
):
    """
    Handle cancelled topup payment.

    This endpoint is called when a user cancels a topup payment.
    It sets the pending topup status to CANCELLED if a session_id is provided.
    """
    session_id = request.query_params.get("session_id")

    if session_id:
        # Find and update the pending topup to cancelled status
        pending_topup = (
            db.query(PendingTopup)
            .filter(PendingTopup.session_id == session_id)
            .filter(PendingTopup.user_id == user.id)
            .first()
        )

        if pending_topup:
            pending_topup.status = PendingTopupStatus.CANCELLED
            db.add(pending_topup)
            db.commit()
            logger.info(
                f"User {user.id} cancelled topup payment for session {session_id}"
            )
        else:
            logger.warning(
                f"No pending topup found for session {session_id} and user {user.id}"
            )
    else:
        logger.info(f"User {user.id} cancelled topup payment (no session_id provided)")

    # Redirect to billing page with cancellation message
    return RedirectResponse(url=f"{settings.app_url}/workspace/billing?cancelled=true")


@app.get("/api/billing/payment-methods", response_model=PaymentMethodsResponse)
def get_payment_methods(
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
):
    """
    Retrieve payment methods for the current user from Stripe.

    This endpoint fetches all payment methods associated with the user's Stripe customer
    and identifies the default payment method.

    Returns:
        PaymentMethodsResponse: List of payment methods with default method identified

    Raises:
        HTTPException: If user account details not found, user not onboarded, or Stripe API error
    """

    if not user.account_details.stripe_customer_id:
        logger.error(f"User {user.id} not onboarded with Stripe")
        raise HTTPException(
            status_code=400, detail="User account not onboarded with Stripe"
        )

    try:
        # Retrieve customer from Stripe to get default payment method
        customer = stripe.Customer.retrieve(user.account_details.stripe_customer_id)
        default_payment_method_id = None
        if (
            customer.invoice_settings
            and customer.invoice_settings.default_payment_method
        ):
            default_payment_method_id = str(
                customer.invoice_settings.default_payment_method
            )

        # List all payment methods for the customer
        payment_methods = stripe.PaymentMethod.list(
            customer=user.account_details.stripe_customer_id, type="card"
        )

        # Convert Stripe payment methods to our response format
        payment_method_data = []
        for pm in payment_methods.data:
            pm_data = PaymentMethodData(
                id=pm.id, type=pm.type, isDefault=(pm.id == default_payment_method_id)
            )

            # Add card-specific information if available
            if pm.card:
                pm_data.card_brand = pm.card.brand
                pm_data.card_last4 = pm.card.last4
                pm_data.card_exp_month = pm.card.exp_month
                pm_data.card_exp_year = pm.card.exp_year

            payment_method_data.append(pm_data)

        logger.info(
            f"Retrieved {len(payment_method_data)} payment methods for user {user.id}"
        )

        return PaymentMethodsResponse(
            paymentMethods=payment_method_data,
            defaultPaymentMethodId=default_payment_method_id,
        )

    except stripe.StripeError as e:
        logger.error(f"Stripe error retrieving payment methods for user {user.id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve payment methods: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving payment methods for user {user.id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve payment methods: {str(e)}"
        )


@app.post(
    "/api/billing/customer-portal-session", response_model=CustomerPortalSessionResponse
)
def create_customer_portal_session(
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
):
    """
    Create a Stripe customer portal session for the current user.

    This endpoint creates a portal session that allows customers to manage their
    billing information, payment methods, and subscription details.

    Returns:
        CustomerPortalSessionResponse: Contains the portal session URL

    Raises:
        HTTPException: If user account details not found, user not onboarded, or Stripe API error
    """

    if not user.account_details.stripe_customer_id:
        logger.error(f"User {user.id} not onboarded with Stripe")
        raise HTTPException(
            status_code=400, detail="User account not onboarded with Stripe"
        )

    try:
        # Create the customer portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=user.account_details.stripe_customer_id,
            return_url=f"{settings.app_url}/workspace/billing",
        )

        logger.info(f"Created customer portal session for user {user.id}")

        return CustomerPortalSessionResponse(url=portal_session.url)

    except stripe.StripeError as e:
        logger.error(
            f"Stripe error creating customer portal session for user {user.id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create customer portal session: {str(e)}",
        )
    except Exception as e:
        logger.error(
            f"Unexpected error creating customer portal session for user {user.id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create customer portal session: {str(e)}",
        )


@app.get("/api/billing/billing-details", response_model=BillingDetailsResponse)
def get_billing_details(
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
):
    """
    Retrieve billing details for the current user from Stripe.

    This endpoint fetches the customer information from Stripe including
    contact details, address, and tax information.

    Returns:
        BillingDetailsResponse: Customer billing details from Stripe

    Raises:
        HTTPException: If user account details not found, user not onboarded, or Stripe API error
    """
    if not user.account_details.stripe_customer_id:
        logger.error(f"User {user.id} not onboarded with Stripe")
        raise HTTPException(
            status_code=400, detail="User account not onboarded with Stripe"
        )

    try:
        # Retrieve customer from Stripe
        customer = stripe.Customer.retrieve(user.account_details.stripe_customer_id)

        # Extract billing details from customer object
        billing_details = BillingDetailsData(
            email=customer.email,
            name=customer.name,
            phone=customer.phone,
            addressLine1=customer.address.line1 if customer.address else None,
            addressLine2=customer.address.line2 if customer.address else None,
            addressCity=customer.address.city if customer.address else None,
            addressState=customer.address.state if customer.address else None,
            addressPostalCode=(
                customer.address.postal_code if customer.address else None
            ),
            addressCountry=customer.address.country if customer.address else None,
            taxId=None,  # Tax ID is typically stored in tax_ids, we could extend this later
        )

        # Get tax IDs if they exist
        if hasattr(customer, "tax_ids") and customer.tax_ids and customer.tax_ids.data:
            # Use the first tax ID if available
            billing_details.tax_id = customer.tax_ids.data[0].value

        logger.info(f"Retrieved billing details for user {user.id}")

        return BillingDetailsResponse(billingDetails=billing_details)

    except stripe.StripeError as e:
        logger.error(f"Stripe error retrieving billing details for user {user.id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve billing details: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving billing details for user {user.id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve billing details: {str(e)}"
        )


@app.post("/api/create-checkout-session")
def stripe_checkout_session(
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Create a Stripe checkout session for a subscription signup.

    This endpoint creates a checkout session for a subscription signup.
    It checks if the user has an active subscription or closed account and redirects accordingly.
    If the user does not have an active subscription or closed account, it creates a checkout session for the subscription signup.
    """

    # Check if user already has an active subscription or closed account
    billing_service = BillingService(db)
    account_status: AccountStatusResponse = billing_service.get_account_status_detailed(
        user
    )

    if account_status.is_closed:
        logger.info(f"User {user.id} has closed account, redirecting to workspace")
        return JSONResponse(
            content={
                "redirect": True,
                "redirect_url": "/workspace",
                "reason": "account_closed",
            },
            status_code=200,
        )

    if account_status.has_active_subscription:
        logger.info(
            f"User {user.id} already has active subscription, redirecting to workspace"
        )
        return JSONResponse(
            content={
                "redirect": True,
                "redirect_url": "/workspace",
                "reason": "active_subscription",
            },
            status_code=200,
        )

    customer_query = stripe.Customer.search(query=f"email:'{user.email}'")
    existing_customers = customer_query.data
    customer = None
    if len(existing_customers) == 1:
        customer = existing_customers[0]
        logger.info(f"found existing stripe customer {customer['id']}")
    elif len(existing_customers) > 1:
        raise Exception("Too many stripe customers returned")
    else:
        logger.info(f"no found existing stripe customer")

    try:
        if customer is not None:
            session = stripe.checkout.Session.create(
                line_items=[
                    {
                        "price": settings.stripe_price_id,
                        "quantity": 1,
                    },
                ],
                mode="subscription",
                ui_mode="custom",
                # The URL of your payment completion page
                return_url=f"{settings.app_url}/workspace/billing/subscription/complete?session_id={{CHECKOUT_SESSION_ID}}",
                customer=customer["id"],
                metadata={
                    "type": "subscription_signup",
                },
            )
        else:
            session = stripe.checkout.Session.create(
                line_items=[
                    {
                        "price": settings.stripe_price_id,
                        "quantity": 1,
                    },
                ],
                mode="subscription",
                ui_mode="custom",
                # The URL of your payment completion page
                return_url=f"{settings.app_url}/workspace/billing/subscription/complete?session_id={{CHECKOUT_SESSION_ID}}",
                customer_email=user.email,
                metadata={
                    "type": "subscription_signup",
                },
            )
        return JSONResponse(
            content=dict(checkoutSessionClientSecret=session["client_secret"])
        )
    except Exception as e:
        logger.exception(f"Error creating checkout session: {e}")
        return JSONResponse(content=dict(error=e), status_code=403)


class SessionStatusRequest(BaseModel):
    session_id: str


@app.get("/api/session-status")
def session_status(
    session_id: str,
    user: User = Depends(dependency_to_override),
    db: Session = Depends(get_db),
) -> JSONResponse:
    session: stripe.checkout.Session = stripe.checkout.Session.retrieve(
        session_id, expand=["payment_intent"]
    )

    user_account_details = (
        db.query(UserAccountDetails)
        .filter(UserAccountDetails.user_id == user.id)
        .first()
    )
    if not user_account_details:
        raise HTTPException(status_code=400, detail="User account details not found")

    if user_account_details.stripe_customer_id is None:
        # We're still waiting for the stripe webhook "customer.subscription.created"
        # that sets the stripe_customer_id
        return JSONResponse(content=dict(status="open"))

    logger.info(f"session: {session}")

    return JSONResponse(content=dict(status=session.status))
