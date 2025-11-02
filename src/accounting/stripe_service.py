import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional

import stripe
from sqlalchemy.orm import Session
from stripe import StripeError

from src.accounting.billing_service import BillingService
from src.accounting.models import UserAccountDetails
from src.models import User

logger = logging.getLogger(__name__)


@dataclass
class RefundBreakdownItem:
    """Represents a single refund operation mapped to an invoice."""

    invoice_id: str
    refund_amount_cents: int
    invoice_amount_cents: int


@dataclass
class RefundResult:
    """Represents the result of a single Stripe refund operation."""

    invoice_id: str
    credit_note_id: Optional[str]
    amount_cents: int
    status: Optional[str]
    success: bool
    error: Optional[str] = None


@dataclass
class CancellationRefundResult:
    """Represents the result of canceling a subscription and processing refunds."""

    subscription_cancelled: bool
    subscription_id: Optional[str]
    refunds_processed: List[RefundResult]
    total_refunded_cents: int
    success: bool
    error: Optional[str] = None


class StripeService:
    """
    Service class for handling Stripe webhook events and business logic.

    This service encapsulates all Stripe-related operations and delegates
    billing operations to the BillingService FSM for proper state management.
    """

    def __init__(self, db: Session):
        self.db = db
        self.billing_service = BillingService(db)

    def _edit_metadata(self, session_data: dict) -> None:
        """
        Edit the metadata of the session data.
        """
        # Verify this is a top-up session
        session_id = session_data.get("id")
        metadata = session_data.get("metadata", {})

        if metadata.get("type") != "account_topup":
            logger.info(f"Session is not a top-up session, skipping")
            return

        if session_data.get("payment_status") != "paid":
            logger.warning(
                f"Session {session_id} payment status is {session_data.get('payment_status')}"
            )
            raise ValueError(
                f"Session {session_id} payment status is {session_data.get('payment_status')}"
            )

        user_id_str = metadata.get("user_id")
        topup_amount_cents_str = metadata.get("topup_amount_cents")
        invoice_id = session_data.get("invoice")
        payment_intent_id = session_data.get("payment_intent")

        if (
            not invoice_id
            or not payment_intent_id
            or not user_id_str
            or not topup_amount_cents_str
        ):
            error_msg = f"Missing required metadata in session {session_id}: invoice_id={invoice_id}, payment_intent_id={payment_intent_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Update invoice metadata to include payment intent ID
        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
        except Exception as e:
            logger.error(f"Error retrieving invoice {invoice_id}: {e}")
            raise

        new_metadata = invoice.metadata or {}
        new_metadata["payment_intent"] = payment_intent_id
        stripe.Invoice.modify(
            id=invoice_id,
            metadata=new_metadata,
        )

        # Update payment intent metadata to include invoice ID
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        new_metadata = payment_intent.metadata or {}
        new_metadata["invoice"] = invoice_id
        stripe.PaymentIntent.modify(
            id=payment_intent_id,
            metadata=new_metadata,
        )

    def handle_checkout_session_completed(self, event: dict) -> None:
        """
        Handle checkout.session.completed events for account top-ups.

        Args:
            event: The Stripe webhook event data

        Raises:
            ValueError: If the event data is invalid or missing required fields
        """
        session_data = event["data"]["object"]
        session_id = session_data["id"]

        logger.info(f"Processing completed checkout session: {session_id}")

        # Verify this is a top-up session
        metadata = session_data.get("metadata", {})
        if metadata.get("type") != "account_topup":
            logger.info(f"Session {session_id} is not a top-up session, skipping")
            return

        self._edit_metadata(session_data)

        # Verify payment was successful
        if session_data.get("payment_status") != "paid":
            logger.warning(
                f"Session {session_id} payment status is {session_data.get('payment_status')}, skipping"
            )
            return

        # Get the invoice download URL
        download_url = self._get_invoice_download_url(session_data)

        # Process the pending top-up using BillingService
        try:
            account_details = self.billing_service.process_pending_topup(
                session_id, success=True, download_url=download_url
            )

            logger.info(
                f"Successfully processed pending top-up for session {session_id}: "
                f"New balance: {account_details.balance_cents} cents, "
                f"Status: {account_details.status}"
            )
        except ValueError as e:
            logger.error(
                f"Failed to process pending top-up for session {session_id}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error processing pending top-up for session {session_id}: {e}"
            )
            raise

    def handle_checkout_session_expired(self, event: dict) -> None:
        """
        Handle checkout.session.expired events for account top-ups.

        Args:
            event: The Stripe webhook event data
        """
        session_data = event["data"]["object"]
        session_id = session_data["id"]

        logger.info(f"Processing expired checkout session: {session_id}")

        # Verify this is a top-up session
        metadata = session_data.get("metadata", {})
        if metadata.get("type") != "account_topup":
            logger.info(f"Session {session_id} is not a top-up session, skipping")
            return

        # Mark the pending top-up as failed
        try:
            self.billing_service.process_pending_topup(
                session_id, download_url=None, success=False
            )
            logger.info(
                f"Marked pending top-up as failed for expired session {session_id}"
            )
        except ValueError as e:
            logger.warning(
                f"No pending top-up found for expired session {session_id}: {e}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error processing expired session {session_id}: {e}"
            )

    def handle_checkout_session_async_payment_failed(self, event: dict) -> None:
        """
        Handle checkout.session.async_payment_failed events for account top-ups.

        Args:
            event: The Stripe webhook event data
        """
        session_data = event["data"]["object"]
        session_id = session_data["id"]

        logger.info(f"Processing async payment failed checkout session: {session_id}")

        # Verify this is a top-up session
        metadata = session_data.get("metadata", {})
        if metadata.get("type") != "account_topup":
            logger.info(f"Session {session_id} is not a top-up session, skipping")
            return

        # Mark the pending top-up as failed
        try:
            self.billing_service.process_pending_topup(
                session_id, download_url=None, success=False
            )
            logger.info(
                f"Marked pending top-up as failed for async payment failed session {session_id}"
            )
        except ValueError as e:
            logger.warning(
                f"No pending top-up found for async payment failed session {session_id}: {e}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error processing async payment failed session {session_id}: {e}"
            )

    def handle_checkout_session_async_payment_succeeded(self, event: dict) -> None:
        """
        Handle checkout.session.async_payment_succeeded events for account top-ups.

        Args:
            event: The Stripe webhook event data

        Raises:
            ValueError: If the event data is invalid or missing required fields
        """
        session_data = event["data"]["object"]
        session_id = session_data["id"]

        logger.info(
            f"Processing async payment succeeded checkout session: {session_id}"
        )

        # Verify this is a top-up session
        metadata = session_data.get("metadata", {})
        if metadata.get("type") != "account_topup":
            logger.info(f"Session {session_id} is not a top-up session, skipping")
            return

        # Extract top-up details
        user_id_str = metadata.get("user_id")
        topup_amount_cents_str = metadata.get("topup_amount_cents")

        if not user_id_str or not topup_amount_cents_str:
            error_msg = f"Missing required metadata in session {session_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            user_id = uuid.UUID(user_id_str)
            topup_amount_cents = int(topup_amount_cents_str)
        except (ValueError, TypeError) as e:
            error_msg = f"Invalid metadata format in session {session_id}: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Verify payment was successful
        if session_data.get("payment_status") != "paid":
            logger.warning(
                f"Session {session_id} payment status is {session_data.get('payment_status')}, skipping"
            )
            return

        # Get the invoice download URL
        download_url = self._get_invoice_download_url(session_data)

        # Process the pending top-up using BillingService
        try:
            account_details = self.billing_service.process_pending_topup(
                session_id, success=True, download_url=download_url
            )

            logger.info(
                f"Successfully processed pending top-up for async payment succeeded session {session_id}: "
                f"user {user_id}, amount {topup_amount_cents} cents. "
                f"New balance: {account_details.balance_cents} cents, "
                f"Status: {account_details.status}"
            )

        except ValueError as e:
            logger.error(
                f"Failed to process pending top-up for async payment succeeded session {session_id}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error processing async payment succeeded session {session_id}: {e}"
            )
            raise

    def get_paid_invoices(self, stripe_customer_id: str) -> List[stripe.Invoice]:
        """Retrieve paid invoices for a Stripe customer ordered newest first.

        Args:
            stripe_customer_id: The Stripe customer ID

        Returns:
            List of paid ``stripe.Invoice`` objects sorted by creation date (newest first).
        """
        try:
            invoices = stripe.Invoice.list(
                customer=stripe_customer_id,
                status="paid",
                limit=100,  # Adjust as needed
            )
            # Sort invoices by creation date (newest first)
            sorted_invoices = sorted(
                invoices.data, key=lambda inv: inv.created, reverse=True
            )
            logger.info(
                "Retrieved %s paid invoices for customer %s",
                len(sorted_invoices),
                stripe_customer_id,
            )
            return sorted_invoices

        except Exception as e:
            logger.error(
                "Unexpected error retrieving invoices for customer %s: %s",
                stripe_customer_id,
                e,
            )
            raise

    def calculate_refund_breakdown(
        self,
        invoices: List[stripe.Invoice],
        refund_amount_cents: int,
    ) -> List[RefundBreakdownItem]:
        """Determine how a refund should be split across a list of invoices.

        The algorithm walks the invoices newest → oldest and allocates as much of the
        requested refund amount as possible from each invoice until the full amount
        is covered.

        Args:
            invoices: Paid invoices sorted newest first.
            refund_amount_cents: Total amount to refund in **cents**.

        Returns:
            List of ``RefundBreakdownItem`` describing the individual refund
            operations that must be performed.

        Raises:
            ValueError: If the sum of the invoice amounts is lower than the refund
                amount requested.
        """
        refund_breakdown: List[RefundBreakdownItem] = []
        remaining_refund = refund_amount_cents

        for invoice in invoices:
            if remaining_refund <= 0:
                break

            invoice_amount = (
                invoice.amount_paid or invoice.amount_due
            )  # amount_paid is safest for paid invoices
            invoice_id = str(invoice.id)

            refund_from_invoice = min(remaining_refund, invoice_amount)

            refund_breakdown.append(
                RefundBreakdownItem(
                    invoice_id=invoice_id,
                    refund_amount_cents=refund_from_invoice,
                    invoice_amount_cents=invoice_amount,
                )
            )

            remaining_refund -= refund_from_invoice

        if remaining_refund > 0:
            raise ValueError(
                f"Insufficient paid invoices to refund {refund_amount_cents} cents. "
                f"Only {refund_amount_cents - remaining_refund} cents available."
            )

        return refund_breakdown

    def create_credit_note_for_refund(
        self,
        invoice: stripe.Invoice,
        refund_amount_cents: int,
        refund_id: str,
        reason: Literal[
            "order_change", "duplicate", "fraudulent", "product_unsatisfactory"
        ] = "order_change",
    ) -> Optional[str]:
        """Create a credit note that corresponds to a *paid* invoice refund.

        Stripe's rules for paid-invoice credit notes require that the *sum* of
        ``refund_amount``, ``credit_amount`` and ``out_of_band_amount`` equals
        the invoice's *post_payment_amount*.  In the simple cash-refund case
        we're handling here, that means we either:

        1. Link the credit note directly to the refund by passing ``refund``.
        2. Or, when the refund hasn't yet been created, pass ``refund_amount``.

        Args:
            invoice_id: ID of the paid invoice.
            refund_amount_cents: Amount that was (or will be) refunded, in cents.
            refund_id: Optional Stripe refund ID if the refund already exists.
            reason: Free-text memo shown on the credit note PDF.
        """

        try:
            payload: Dict[str, Any] = {
                "invoice": str(invoice.id),
                "reason": reason,
                "memo": reason,
                "lines": [
                    {
                        "amount": refund_amount_cents,
                        "description": "Refund",
                        "type": "invoice_line_item",
                        "invoice_line_item": invoice.lines.data[0].id,
                    }
                ],
            }

            if refund_id:
                payload["refunds"] = [{"refund": refund_id}]
            else:
                payload["refund_amount"] = refund_amount_cents

            credit_note = stripe.CreditNote.create(**payload)

            logger.info(
                "Created credit note %s for invoice %s (%s cents)",
                credit_note.id,
                invoice.id,
                refund_amount_cents,
            )
            return credit_note.id

        except Exception as e:
            logger.error(
                "Failed to create credit note for invoice %s: %s", invoice.id, e
            )
            return None

    def process_refunds(
        self, refund_breakdown: List[RefundBreakdownItem]
    ) -> List[RefundResult]:
        """
        Process refunds through Stripe for the given breakdown.

        Args:
            refund_breakdown: List of refund operations to perform

        Returns:
            List of refund results with Stripe refund IDs and statuses
        """
        refund_results = []

        for refund_op in refund_breakdown:
            try:
                invoice_id = refund_op.invoice_id
                refund_amount = refund_op.refund_amount_cents

                # Retrieve the invoice to ensure it exists (and to log useful context)
                invoice = stripe.Invoice.retrieve(invoice_id)

                # Create a credit note that automatically issues a refund for the charge
                #   Ref: https://docs.stripe.com/invoicing/integration/programmatic-credit-notes#paid-invoices
                credit_note = stripe.CreditNote.create(
                    invoice=invoice_id,
                    # Create a single custom line item for the refund. Using a custom line item avoids
                    # needing to fetch specific invoice line items while still associating the credit
                    # note with the invoice.
                    lines=[
                        {
                            "type": "custom_line_item",
                            "description": "Automated refund via credit note",
                            "quantity": 1,
                            "unit_amount": refund_amount,
                        }
                    ],
                    refund_amount=refund_amount,
                    reason="order_change",
                    memo="Automated refund issued by StripeService.process_refunds",
                )

                refund_results.append(
                    RefundResult(
                        invoice_id=refund_op.invoice_id,
                        credit_note_id=credit_note.id,
                        amount_cents=refund_amount,
                        status=getattr(credit_note, "status", None),
                        success=getattr(credit_note, "status", "") == "issued",
                    )
                )

                logger.info(
                    f"Created credit note {credit_note.id} (status={credit_note.status}) for invoice {invoice_id}: {refund_amount} cents",
                )

            except Exception as e:
                logger.error(
                    f"Unexpected error creating refund for invoice {refund_op.invoice_id}: {e}"
                )
                refund_results.append(
                    RefundResult(
                        invoice_id=refund_op.invoice_id,
                        credit_note_id=None,
                        amount_cents=refund_op.refund_amount_cents,
                        status="failed",
                        success=False,
                        error=str(e),
                    )
                )

        return refund_results

    def create_subscription(
        self, stripe_customer_id: str, price_id: str
    ) -> stripe.Subscription:
        """
        Create a Stripe subscription for a customer using their default payment method.

        This method creates a subscription directly using the customer's default payment method,
        which should have been set up during the initial checkout session for payment method collection.

        Args:
            stripe_customer_id: The Stripe customer ID
            price_id: The Stripe price ID for the subscription

        Returns:
            stripe.Subscription: The created subscription object

        Raises:
            Exception: If subscription creation fails
        """
        try:
            # Create the subscription using the customer's default payment method
            subscription = stripe.Subscription.create(
                customer=stripe_customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                payment_settings={"save_default_payment_method": "on_subscription"},
                expand=["latest_invoice.payment_intent"],
            )

            logger.info(
                f"Successfully created Stripe subscription {subscription.id} "
                f"for customer {stripe_customer_id} with price {price_id}. "
                f"Status: {subscription.status}"
            )

            return subscription

        except Exception as e:
            logger.error(
                f"Failed to create Stripe subscription for customer {stripe_customer_id}: {e}"
            )
            raise

    def _get_invoice_download_url(self, session_data: dict) -> Optional[str]:
        """
        Get the invoice download URL from a Stripe checkout session.

        Args:
            session_data: The Stripe checkout session data

        Returns:
            Optional[str]: The invoice download URL if available, None otherwise
        """
        invoice_id = session_data.get("invoice")
        if not invoice_id:
            logger.warning(f"No invoice ID found in session {session_data.get('id')}")
            raise ValueError(f"No invoice ID found in session {session_data.get('id')}")

        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            download_url = getattr(invoice, "hosted_invoice_url", None)

            if download_url:
                logger.info(f"Retrieved invoice download URL for invoice {invoice_id}")
            else:
                logger.error(
                    f"No hosted invoice URL available for invoice {invoice_id}"
                )
                raise ValueError(
                    f"No hosted invoice URL available for invoice {invoice_id}"
                )

            return download_url

        except Exception as e:
            logger.error(f"Error retrieving invoice {invoice_id} for download URL: {e}")
            return None

    def handle_setup_intent_succeeded(self, event: dict) -> None:
        """
        Handle setup_intent.succeeded events for subscription payment setup.

        After a successful setup intent, this creates the OpenMeter customer and
        Stripe subscription for the user.

        Args:
            event: The Stripe webhook event data
        """
        setup_intent_data = event["data"]["object"]
        setup_intent_id = setup_intent_data["id"]

        logger.info(f"Processing succeeded setup intent: {setup_intent_id}")

        # Verify this is a subscription setup intent
        metadata = setup_intent_data.get("metadata", {})
        if metadata.get("type") != "subscription_setup":
            logger.info(
                f"Setup intent {setup_intent_id} is not for subscription setup, skipping"
            )
            return

        user_id_str = metadata.get("user_id")
        if not user_id_str:
            logger.error(f"No user_id found in setup intent {setup_intent_id} metadata")
            return

        try:
            from uuid import UUID

            from src.models import User

            user_id = UUID(user_id_str)
            user = self.db.query(User).filter(User.id == user_id).first()

            if not user:
                logger.error(
                    f"User {user_id} not found for setup intent {setup_intent_id}"
                )
                return

            user_account_details = user.account_details
            stripe_customer_id = user_account_details.stripe_customer_id

            if not stripe_customer_id:
                logger.error(
                    f"User {user_id} has no Stripe customer ID for setup intent {setup_intent_id}"
                )
                return

            # Set the payment method as the default for the customer
            payment_method_id = setup_intent_data.get("payment_method")
            if payment_method_id:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=stripe_customer_id,
                )

                # Set as default payment method
                stripe.Customer.modify(
                    stripe_customer_id,
                    invoice_settings={"default_payment_method": payment_method_id},
                )

            # Create OpenMeter customer via the checkout session API
            # This creates both OpenMeter customer and handles the integration
            from src.accounting.openmeter_service import OpenMeterService
            from src.config import settings

            # openmeter_service = OpenMeterService(
            #     base_url=settings.openmeter_base_url,
            #     api_token=settings.openmeter_api_token,
            # )
            # try:
            #     # Create OpenMeter customer and attribute usage
            #     # Note: We don't need the checkout session URL, just the customer creation
            #     openmeter_response = openmeter_service.create_checkout_session(
            #         customer_name=user.name,
            #         customer_key=str(user.id),
            #         subject_keys=[str(user.id)],
            #         success_url=f"{settings.app_url}/workspace/billing/subscription/complete",
            #         currency="USD",
            #         mode="setup",
            #     )
            #     logger.info(
            #         f"Created OpenMeter customer {openmeter_response.customer_id} for user {user_id}"
            #     )
            # except Exception as openmeter_error:
            #     logger.warning(
            #         f"Failed to create OpenMeter customer for user {user_id}, "
            #         f"continuing with subscription creation: {openmeter_error}"
            #     )
            # Create the subscription using our existing method
            subscription = self.create_subscription(
                stripe_customer_id=stripe_customer_id,
                price_id=settings.stripe_price_id,
            )

            # Complete onboarding
            from src.accounting import accounting_controller

            accounting_controller.complete_onboarding(user, self.db)

            logger.info(
                f"Successfully completed subscription setup for user {user_id}. "
                f"Setup intent: {setup_intent_id}, Subscription: {subscription.id}"
            )

        except Exception as e:
            logger.error(
                f"Failed to complete subscription setup for setup intent {setup_intent_id}: {e}"
            )

    def handle_subscription_created(self, event: dict) -> None:
        """
        Handle customer.subscription.created events.

        This handler saves the Stripe customer ID to the UserAccountDetails for the user.
        If no existing connected user is found, it uses the Stripe customer email to
        look up and connect the user. Assumes 1-to-1 mapping of email to Stripe customer.

        Args:
            event: The Stripe webhook event data

        Raises:
            ValueError: If the event data is invalid or missing required fields
        """
        subscription_data = event["data"]["object"]
        subscription_id = subscription_data["id"]
        customer_id = subscription_data.get("customer")

        logger.info(
            f"Processing customer.subscription.created event for subscription: {subscription_id}"
        )

        if not customer_id:
            error_msg = f"No customer ID found in subscription {subscription_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # Retrieve customer details from Stripe to get email
            customer = stripe.Customer.retrieve(customer_id)
            customer_email = customer.email

            if not customer_email:
                logger.error(f"No email found for Stripe customer {customer_id}")
                return

            logger.info(
                f"Retrieved customer {customer_id} with email: {customer_email}"
            )

            # Find user by email
            from src.models import User

            user = self.db.query(User).filter(User.email == customer_email).first()

            if not user:
                logger.warning(
                    f"No user found with email {customer_email} for customer {customer_id}. "
                    f"User needs to be registered before subscription creation."
                )
                return

            # Get or ensure UserAccountDetails exists
            user_account_details = user.account_details
            if not user_account_details:
                logger.error(f"No UserAccountDetails found for user {user.id}")
                return

            # Check if customer ID is already set (idempotency)
            if user_account_details.stripe_customer_id == customer_id:
                logger.info(
                    f"Stripe customer ID {customer_id} already set for user {user.id}, "
                    f"skipping duplicate webhook"
                )
                return

            if user_account_details.stripe_customer_id:
                logger.warning(
                    f"User {user.id} already has different Stripe customer ID: "
                    f"{user_account_details.stripe_customer_id}, updating to {customer_id}"
                )

            # Save the customer ID
            user_account_details.stripe_customer_id = customer_id
            self.db.add(user_account_details)
            self.db.commit()

            logger.info(
                f"Successfully saved Stripe customer ID {customer_id} to UserAccountDetails "
                f"for user {user.id} ({customer_email})"
            )

        except StripeError as e:
            logger.error(f"Stripe API error retrieving customer {customer_id}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error processing subscription created for customer {customer_id}: {e}"
            )
            # Rollback the transaction on error
            self.db.rollback()
            raise

    def handle_subscription_deleted_through_stripe_portal(self, event: dict) -> None:
        """
        Handle customer.subscription.deleted events from Stripe Customer Portal.

        When customers cancel their subscription through the Stripe Customer Portal,
        the subscription is already canceled in Stripe. This handler:
        1. Finds the user by customer email
        2. Cancels the subscription in our billing service to downgrade the account
        3. Refunds the most recent invoice for the canceled subscription

        Args:
            event: The Stripe webhook event data

        Raises:
            ValueError: If the event data is invalid or missing required fields
        """
        subscription_data = event["data"]["object"]
        subscription_id = subscription_data["id"]
        customer_id = subscription_data.get("customer")

        logger.info(
            f"Processing customer.subscription.deleted event for subscription: {subscription_id}"
        )

        if not customer_id:
            error_msg = f"No customer ID found in subscription {subscription_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # Retrieve customer details from Stripe to get email
            customer = stripe.Customer.retrieve(customer_id)
            logger.info(
                f"Retrieved customer {customer_id} with email: {customer.email}"
            )

            user_account_details: UserAccountDetails | None = (
                self.db.query(UserAccountDetails)
                .filter(UserAccountDetails.stripe_customer_id == customer_id)
                .first()
            )

            if not user_account_details:
                logger.error(
                    f"No user account details found for customer {customer_id}. "
                    f"Subscription {subscription_id} was canceled but user account cannot be downgraded."
                )
                return

            user: User = user_account_details.user

            if not user:
                logger.error(
                    f"No user found for customer {customer_id}. "
                    f"Subscription {subscription_id} was canceled but user account cannot be downgraded."
                )
                return

            # Cancel subscription in billing service to downgrade account
            external_id = (
                f"portal_cancel_{subscription_id}_{int(datetime.now().timestamp())}"
            )
            try:
                self.billing_service.cancel_subscription(
                    user=user, external_id=external_id
                )
                logger.info(
                    f"Successfully canceled subscription in billing service for user {user.id} "
                    f"(customer {customer_id}, subscription {subscription_id})"
                )
            except Exception as billing_error:
                logger.error(
                    f"Failed to cancel subscription in billing service for user {user.id}: {billing_error}"
                )
                # Continue with refund processing even if billing cancellation fails
                # to ensure customer gets refunded

            # Refund the most recent invoice for this subscription
            try:
                refund_results = self.refund_most_recent_subscription_invoice(
                    subscription_id=subscription_id, stripe_customer_id=customer_id
                )

                total_refunded_cents = sum(
                    result.amount_cents for result in refund_results if result.success
                )

                if refund_results:
                    logger.info(
                        f"Successfully processed {total_refunded_cents} cents in refunds "
                        f"for canceled subscription {subscription_id} (user {user.id})"
                    )
                else:
                    logger.info(
                        f"No refunds processed for canceled subscription {subscription_id} "
                        f"(user {user.id}) - no recent invoices or already refunded"
                    )

            except Exception as refund_error:
                logger.error(
                    f"Failed to process refund for canceled subscription {subscription_id}: {refund_error}"
                )
                # Don't raise - webhook should succeed even if refund fails

        except StripeError as e:
            logger.error(f"Stripe API error retrieving customer {customer_id}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error processing subscription deletion for customer {customer_id}: {e}"
            )
            # Rollback the transaction on error
            self.db.rollback()
            raise

    def find_active_subscription(
        self, stripe_customer_id: str
    ) -> Optional[stripe.Subscription]:
        """
        Find the first active subscription for a Stripe customer.

        Args:
            stripe_customer_id: The Stripe customer ID

        Returns:
            The active subscription object if found, None otherwise
        """
        try:
            subscriptions = stripe.Subscription.list(
                customer=stripe_customer_id, status="active", limit=1
            )

            if subscriptions.data:
                subscription = subscriptions.data[0]
                logger.info(
                    f"Found active subscription {subscription.id} for customer {stripe_customer_id}"
                )
                return subscription
            else:
                logger.info(
                    f"No active subscription found for customer {stripe_customer_id}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Error finding active subscription for customer {stripe_customer_id}: {e}"
            )
            raise

    def cancel_subscription(self, subscription_id: str) -> stripe.Subscription:
        """
        Cancel a Stripe subscription immediately.

        Args:
            subscription_id: The ID of the subscription to cancel

        Returns:
            The canceled subscription object

        Raises:
            Exception: If subscription cancellation fails
        """
        try:
            canceled_subscription = stripe.Subscription.delete(subscription_id)

            logger.info(
                f"Successfully canceled Stripe subscription {subscription_id}. "
                f"Status: {canceled_subscription.status}"
            )

            return canceled_subscription

        except Exception as e:
            logger.error(f"Failed to cancel Stripe subscription {subscription_id}: {e}")
            raise

    def get_paid_invoices_with_filters(
        self,
        stripe_customer_id: str,
        subscription_id: Optional[str] = None,
        since_days: Optional[int] = None,
    ) -> List[stripe.Invoice]:
        """
        Retrieve paid invoices for a Stripe customer with optional filtering.

        Args:
            stripe_customer_id: The Stripe customer ID
            subscription_id: Optional subscription ID to filter invoices
            since_days: Optional number of days to look back for invoices

        Returns:
            List of paid stripe.Invoice objects sorted by creation date (newest first)
        """
        try:
            # Build query parameters
            query_params = {
                "customer": stripe_customer_id,
                "status": "paid",
                "limit": 100,
            }

            # Add subscription filter if provided
            if subscription_id:
                query_params["subscription"] = subscription_id

            # Add date filter if provided
            if since_days:
                cutoff_date = datetime.now() - timedelta(days=since_days)
                query_params["created"] = {"gte": int(cutoff_date.timestamp())}

            invoices = stripe.Invoice.list(**query_params)

            # Sort invoices by creation date (newest first)
            sorted_invoices = sorted(
                invoices.data, key=lambda inv: inv.created, reverse=True
            )

            logger.info(
                f"Retrieved {len(sorted_invoices)} paid invoices for customer {stripe_customer_id}"
                f"{f' (subscription: {subscription_id})' if subscription_id else ''}"
                f"{f' (since {since_days} days ago)' if since_days else ''}"
            )

            return sorted_invoices

        except Exception as e:
            logger.error(
                f"Error retrieving filtered invoices for customer {stripe_customer_id}: {e}"
            )
            raise

    def refund_most_recent_subscription_invoice(
        self, subscription_id: str, stripe_customer_id: str
    ) -> List[RefundResult]:
        """
        Refund the most recent paid invoice for a subscription if it hasn't been refunded already.

        This method:
        1. Gets the most recent paid invoice for the subscription
        2. Checks if it has already been refunded (has credit notes)
        3. Processes a full refund of the invoice if needed

        Args:
            subscription_id: The Stripe subscription ID
            stripe_customer_id: The Stripe customer ID

        Returns:
            List[RefundResult]: List of refund results (empty if no invoice or already refunded)

        Raises:
            Exception: If refund processing fails
        """
        try:
            # Get the most recent paid invoice for this subscription
            try:
                recent_invoices = stripe.Invoice.list(
                    customer=stripe_customer_id,
                    subscription=subscription_id,
                    status="paid",
                    limit=1,
                )
                most_recent_invoice = (
                    recent_invoices.data[0] if recent_invoices.data else None
                )
            except Exception as e:
                logger.error(
                    f"Failed to retrieve invoices for subscription {subscription_id}: {e}"
                )
                raise

            if not most_recent_invoice:
                logger.info(
                    f"No recent paid invoices found for subscription {subscription_id}"
                )
                return []

            # Check if invoice already has credit notes (indicating previous refunds)
            credit_notes = stripe.CreditNote.list(
                invoice=most_recent_invoice.id, limit=1
            )
            if credit_notes.data:
                logger.info(
                    f"Invoice {most_recent_invoice.id} already has credit notes, skipping refund"
                )
                return []

            # Create refund for the full invoice amount
            invoice_amount = (
                most_recent_invoice.amount_paid or most_recent_invoice.amount_due
            )

            refund_breakdown = [
                RefundBreakdownItem(
                    invoice_id=most_recent_invoice.id,
                    refund_amount_cents=invoice_amount,
                    invoice_amount_cents=invoice_amount,
                )
            ]

            refund_results = self.process_refunds(refund_breakdown)
            total_refunded_cents = sum(
                result.amount_cents for result in refund_results if result.success
            )

            logger.info(
                f"Processed refund of {total_refunded_cents} cents for invoice "
                f"{most_recent_invoice.id} on subscription {subscription_id}"
            )

            return refund_results

        except Exception as e:
            logger.error(
                f"Failed to process refund for most recent invoice on subscription {subscription_id}: {e}"
            )
            raise

    def cancel_and_refund_subscription(
        self, stripe_customer_id: str, refund_last_n_days: int = 30
    ) -> CancellationRefundResult:
        """
        Cancel a customer's active subscription and refund the most recent invoice.

        This method:
        1. Finds the customer's active subscription
        2. Cancels the subscription
        3. Refunds the most recent invoice if it hasn't been refunded already

        Args:
            stripe_customer_id: The Stripe customer ID
            refund_last_n_days: Number of days to look back for refundable payments (unused but kept for API compatibility)

        Returns:
            CancellationRefundResult with details of the operation
        """
        try:
            # Step 1: Find active subscription
            subscription = self.find_active_subscription(stripe_customer_id)
            if not subscription:
                return CancellationRefundResult(
                    subscription_cancelled=False,
                    subscription_id=None,
                    refunds_processed=[],
                    total_refunded_cents=0,
                    success=False,
                    error="No active subscription found for customer",
                )

            subscription_id = subscription.id

            # Step 2: Cancel the subscription
            try:
                canceled_subscription = self.cancel_subscription(subscription_id)
                logger.info(f"Successfully canceled subscription {subscription_id}")
            except Exception as e:
                return CancellationRefundResult(
                    subscription_cancelled=False,
                    subscription_id=subscription_id,
                    refunds_processed=[],
                    total_refunded_cents=0,
                    success=False,
                    error=f"Failed to cancel subscription: {str(e)}",
                )

            # Step 3: Refund the most recent invoice if it exists and hasn't been refunded
            try:
                refund_results = self.refund_most_recent_subscription_invoice(
                    subscription_id=subscription_id,
                    stripe_customer_id=stripe_customer_id,
                )
                total_refunded_cents = sum(
                    result.amount_cents for result in refund_results if result.success
                )
            except Exception as refund_error:
                logger.error(
                    f"Failed to process refund for subscription {subscription_id}: {refund_error}"
                )
                # Subscription is already canceled, but refund failed
                return CancellationRefundResult(
                    subscription_cancelled=True,
                    subscription_id=subscription_id,
                    refunds_processed=[],
                    total_refunded_cents=0,
                    success=False,
                    error=f"Subscription canceled but refund failed: {str(refund_error)}",
                )

            logger.info(
                f"Successfully canceled subscription {subscription_id} and processed "
                f"{total_refunded_cents} cents in refunds for customer {stripe_customer_id}"
            )

            return CancellationRefundResult(
                subscription_cancelled=True,
                subscription_id=subscription_id,
                refunds_processed=refund_results,
                total_refunded_cents=total_refunded_cents,
                success=True,
                error=None,
            )

        except Exception as e:
            logger.error(
                f"Unexpected error in cancel_and_refund_subscription for customer {stripe_customer_id}: {e}"
            )
            return CancellationRefundResult(
                subscription_cancelled=False,
                subscription_id=None,
                refunds_processed=[],
                total_refunded_cents=0,
                success=False,
                error=f"Unexpected error: {str(e)}",
            )

    def handle_subscription_updated(self, event: dict) -> None:
        """
        Handle customer.subscription.updated events for subscription cancellations.

        When users cancel subscriptions through Stripe Customer Portal, the subscription
        remains active until period end and Stripe sends an update event with cancellation
        details instead of a delete event.

        Args:
            event: The Stripe webhook event data

        Raises:
            ValueError: If the event data is invalid or missing required fields
        """
        subscription_data = event["data"]["object"]
        subscription_id = subscription_data["id"]
        customer_id = subscription_data.get("customer")

        logger.info(
            f"Processing customer.subscription.updated event for subscription: {subscription_id}"
        )

        if not customer_id:
            error_msg = f"No customer ID found in subscription {subscription_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # Find user account by stripe customer ID
            user_account_details: UserAccountDetails | None = (
                self.db.query(UserAccountDetails)
                .filter(UserAccountDetails.stripe_customer_id == customer_id)
                .first()
            )

            if not user_account_details:
                logger.error(
                    f"No user account details found for customer {customer_id}. "
                    f"Subscription {subscription_id} update cannot be processed."
                )
                return

            # Check for cancellation details in the event
            cancel_at = subscription_data.get("cancel_at")
            canceled_at = subscription_data.get("canceled_at")
            cancel_at_period_end = subscription_data.get("cancel_at_period_end")

            if cancel_at or canceled_at:
                # Subscription has cancellation scheduled
                user_account_details.subscription_cancel_at = (
                    datetime.fromtimestamp(cancel_at) if cancel_at else None
                )
                user_account_details.subscription_canceled_at = (
                    datetime.fromtimestamp(canceled_at) if canceled_at else None
                )
                user_account_details.subscription_cancel_at_period_end = (
                    cancel_at_period_end
                )

                logger.info(
                    f"Updated subscription cancellation details for user {user_account_details.user_id}: "
                    f"cancel_at={user_account_details.subscription_cancel_at}, "
                    f"canceled_at={user_account_details.subscription_canceled_at}, "
                    f"cancel_at_period_end={cancel_at_period_end}"
                )
            else:
                # Check if cancellation was removed (subscription reactivated)
                if (
                    user_account_details.subscription_cancel_at is not None
                    or user_account_details.subscription_canceled_at is not None
                ):
                    # Clear cancellation details as subscription was reactivated
                    user_account_details.subscription_cancel_at = None
                    user_account_details.subscription_canceled_at = None
                    user_account_details.subscription_cancel_at_period_end = None

                    logger.info(
                        f"Cleared subscription cancellation details for user {user_account_details.user_id} "
                        f"- subscription {subscription_id} was reactivated"
                    )

            # Save changes
            self.db.add(user_account_details)
            self.db.commit()

            logger.info(
                f"Successfully processed subscription.updated event for subscription {subscription_id} "
                f"(customer {customer_id})"
            )

        except StripeError as e:
            logger.error(
                f"Stripe API error processing subscription update {subscription_id}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error processing subscription update for subscription {subscription_id}: {e}"
            )
            # Rollback the transaction on error
            self.db.rollback()
            raise
