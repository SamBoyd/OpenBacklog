"""
OpenMeter service for simplified checkout experience.

This module provides functionality to create OpenMeter customers, attribute usage,
and generate Stripe checkout URLs in a single API call.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field

from src.config import settings
from src.models import User

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """Simple token bucket rate limiter for single-threaded use."""

    def __init__(self, rate: float, burst_capacity: int = None):
        """
        Initialize the rate limiter.

        Args:
            rate: Maximum requests per second
            burst_capacity: Maximum number of tokens in bucket (defaults to rate)
        """
        self.rate = rate
        self.burst_capacity = burst_capacity or int(rate)
        self.tokens = float(self.burst_capacity)
        self.last_refill = time.time()

    def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limit."""
        current_time = time.time()

        # Refill tokens based on elapsed time
        elapsed = current_time - self.last_refill
        self.tokens = min(self.burst_capacity, self.tokens + elapsed * self.rate)
        self.last_refill = current_time

        # If we have tokens, consume one and continue
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return

        # Calculate wait time needed
        wait_time = (1.0 - self.tokens) / self.rate
        logger.debug(f"Rate limit exceeded, waiting {wait_time:.3f} seconds")
        time.sleep(wait_time)

        # Update state after waiting
        self.tokens = 0.0
        self.last_refill = time.time()


class UsageAttribution(BaseModel):
    """Model for usage attribution configuration."""

    subject_keys: List[str] = Field(
        alias="subjectKeys", description="The subject keys in the usage event"
    )


class CustomerData(BaseModel):
    """Model for customer data in checkout session creation."""

    name: str = Field(description="Customer name")
    key: Optional[str] = Field(
        default=None, description="Optional customer key for easier lookup"
    )
    usage_attribution: Optional[UsageAttribution] = Field(
        alias="usageAttribution",
        default=None,
        description="Usage attribution configuration",
    )


class OpenMeterCustomerBillingAddress(BaseModel):
    """Model for customer billing address."""

    country: str = Field(description="Country")
    postalCode: str = Field(description="Postal code")
    state: str = Field(description="State")
    city: str = Field(description="City")
    line1: str = Field(description="Line 1")
    line2: str = Field(description="Line 2")
    phoneNumber: str = Field(description="Phone number")


class OpenMeterCreateCustomerUsageAttribution(BaseModel):
    """Model for creating a customer usage attribution in OpenMeter."""

    subjectKeys: List[str] = Field(description="Subject keys")


class OpenMeterCreateCustomerRequest(BaseModel):
    """Model for creating a customer in OpenMeter."""

    name: str = Field(description="Customer name")
    # description: Optional[str] = Field(description="Customer description")
    metadata: Optional[Dict[str, str]] = Field(description="Customer metadata")
    key: Optional[str] = Field(description="Customer key")
    usageAttribution: Optional[OpenMeterCreateCustomerUsageAttribution] = Field(
        description="Usage attribution configuration"
    )
    primaryEmail: Optional[str] = Field(description="Customer primary email")
    # currency: Optional[str] = Field(description="Customer currency")
    # billingAddress: Optional[OpenMeterCustomerBillingAddress] = Field(description="Customer billing address")


class CheckoutOptions(BaseModel):
    """Model for checkout session options."""

    success_url: str = Field(
        description="URL to redirect to after successful checkout", alias="successUrl"
    )
    currency: str = Field(
        default="USD", description="Currency for the checkout session"
    )
    mode: str = Field(default="setup", description="Checkout session mode")


class CreateCheckoutSessionRequest(BaseModel):
    """Model for creating a Stripe checkout session."""

    customer: CustomerData = Field(description="Customer data")
    options: CheckoutOptions = Field(description="Checkout options")


class CreateCheckoutSessionResult(BaseModel):
    """Model for the response from creating a checkout session."""

    customer_id: str = Field(alias="customerId", description="OpenMeter customer ID")
    stripe_customer_id: str = Field(
        alias="stripeCustomerId", description="Stripe customer ID"
    )
    session_id: str = Field(alias="sessionId", description="Stripe session ID")
    setup_intent_id: str = Field(
        alias="setupIntentId", description="Stripe setup intent ID"
    )
    url: str = Field(description="Stripe checkout URL")
    mode: str = Field(description="Checkout session mode")
    cancel_url: Optional[str] = Field(
        alias="cancelURL", default=None, description="Cancel URL"
    )
    success_url: Optional[str] = Field(
        alias="successURL", default=None, description="Success URL"
    )
    return_url: Optional[str] = Field(
        alias="returnURL", default=None, description="Return URL"
    )


class OpenMeterTokenResponse(BaseModel):
    id: str = Field(description="OpenMeter token ID")
    subject: str = Field(description="OpenMeter token subject")
    expiresAt: str = Field(description="OpenMeter token expires at")
    token: str = Field(description="OpenMeter token")
    allowedMeterSlugs: List[str] = Field(
        description="OpenMeter token allowed meter slugs"
    )


class MeterQueryResponse(BaseModel):
    """Model for meter query response from OpenMeter."""

    id: str = Field(description="Meter ID")
    slug: str = Field(description="Meter slug")
    name: str = Field(description="Meter name")
    description: str = Field(description="Meter description")
    aggregation: str = Field(description="Aggregation type")
    eventType: str = Field(description="Event type")
    valueProperty: str = Field(description="Value property")
    groupBy: Dict[str, str] = Field(description="Group by configuration")
    createdAt: str = Field(description="Created at timestamp")
    updatedAt: str = Field(description="Updated at timestamp")


class UsageQueryResult(BaseModel):
    """Model for usage query result."""

    data: List[Dict[str, Any]] = Field(description="Usage data points")
    from_: Optional[str] = Field(
        alias="from", default=None, description="Query start time"
    )
    to: Optional[str] = Field(default=None, description="Query end time")
    subject: str = Field(description="Subject (user) ID")
    meter: str = Field(description="Meter slug")


class OpenMeterService:
    """Service for interacting with OpenMeter API."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        checkout_rate_limit: float = 48.0,  # Free plan allows for 50 requests per minute & we'll allow room for refund processing which also checks usage
        checkout_burst_capacity: int = 10,
    ):
        """
        Initialize the OpenMeter service.

        Args:
            base_url: OpenMeter API base URL
            api_token: OpenMeter API token
            checkout_rate_limit: Rate limit for checkout sessions (requests/second)
            checkout_burst_capacity: Burst capacity for checkout sessions
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
                "Accept": "*/*",
            }
        )
        self.checkout_rate_limiter = TokenBucketRateLimiter(
            rate=checkout_rate_limit, burst_capacity=checkout_burst_capacity
        )

    def create_customer(self, user: User, stripe_customer_id: str):
        """
        Create an OpenMeter customer.
        """

        existing_customer = self.get_customer_by_key(str(user.id))
        if existing_customer:
            logger.info(
                f"OpenMeter customer {existing_customer['id']} already exists for user {user.id}"
            )
            return existing_customer["id"]

        subject_data = {
            "key": str(user.id),
            "displayName": user.name,
            "metadata": {"externalId": str(user.id)},
            "stripeCustomerId": stripe_customer_id,
        }
        logger.info(f"Creating OpenMeter subject: {subject_data}")
        subject_create_response = self.session.post(
            f"{self.base_url}/api/v1/subjects",
            json=[subject_data],
        )
        if subject_create_response.status_code != 200:
            logger.error(
                f"Failed to create OpenMeter subject: {subject_create_response.json()}"
            )
            subject_create_response.raise_for_status()

        customer_id = str(user.id)

        logger.info(
            f"Successfully created OpenMeter customer {customer_id} for user {user.id}"
        )

        return customer_id

    def create_checkout_session(
        self,
        customer_name: str,
        success_url: str,
        customer_key: Optional[str] = None,
        subject_keys: Optional[List[str]] = None,
        currency: str = "USD",
        mode: str = "setup",
    ) -> CreateCheckoutSessionResult:
        """
        Create a simplified checkout session with OpenMeter for payment method collection.

        This function creates an OpenMeter customer, attributes usage, creates a Stripe customer,
        and generates a Stripe checkout URL in setup mode for collecting payment methods.

        Args:
            customer_name: Name of the customer
            success_url: URL to redirect to after successful checkout
            customer_key: Optional customer key for easier lookup
            subject_keys: Optional list of subject keys for usage attribution
            currency: Currency for the checkout session (default: USD)
            mode: Checkout session mode (default: setup)

        Returns:
            CreateCheckoutSessionResult containing the checkout session details

        Raises:
            requests.RequestException: If the API request fails
            ValueError: If the response is invalid
        """
        try:
            # Prepare the request payload
            customer_data = CustomerData(
                name=customer_name,
                key=customer_key,
                usageAttribution=(
                    UsageAttribution(subjectKeys=subject_keys) if subject_keys else None
                ),
            )

            options = CheckoutOptions(
                successUrl=success_url,
                currency=currency,
                mode=mode,
            )

            request_data = CreateCheckoutSessionRequest(
                customer=customer_data, options=options
            )

            logger.info(
                f"Creating checkout session for customer '{customer_name}' in {mode} mode"
            )
            logger.info(f"Request data: {request_data.model_dump(by_alias=True)}")

            # Make the API request
            url = f"{self.base_url}/api/v1/stripe/checkout/sessions"
            response = self.session.post(
                url, json=request_data.model_dump(by_alias=True)
            )

            # Handle HTTP errors
            response.raise_for_status()

            # Parse and validate the response
            response_data = response.json()
            result = CreateCheckoutSessionResult(**response_data)

            logger.info(
                f"Successfully created checkout session for customer '{customer_name}'. "
                f"Customer ID: {result.customer_id}, Session ID: {result.session_id}"
            )

            return result

        except requests.RequestException as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating checkout session: {e}")
            raise ValueError(f"Invalid response from OpenMeter API: {e}")

    def get_portal_token(self, user_id: str) -> OpenMeterTokenResponse:
        """
        Get a portal token for the given user ID.
        """
        response = requests.post(
            "https://openmeter.cloud/api/v1/portal/tokens",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_token}",
            },
            json={
                "subject": user_id,
                "allowedMeterSlugs": [
                    "cost_total",
                    "input_tokens_total",
                    "output_tokens_total",
                ],
            },
        )

        logger.info(f"OpenMeter token response: {response.json()}")

        response.raise_for_status()
        return OpenMeterTokenResponse(**response.json())

    def get_meter_info(self, meter_slug: str) -> MeterQueryResponse:
        """
        Get meter information from OpenMeter.

        Args:
            meter_slug: The meter slug to query

        Returns:
            MeterQueryResponse containing meter details
        """
        url = f"{self.base_url}/api/v1/meters/{meter_slug}"
        response = self.session.get(url)
        response.raise_for_status()
        return MeterQueryResponse(**response.json())

    def query_usage(
        self,
        subject: str,
        meter_slug: str,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
        window_size: str = "MINUTE",
        window_time_zone: str = "UTC",
    ) -> UsageQueryResult:
        """
        Query usage data for a specific subject and meter.

        Args:
            subject: The subject (user) ID to query usage for
            meter_slug: The meter slug to query
            from_time: Optional start time in ISO format
            to_time: Optional end time in ISO format
            window_size: Window size for aggregation (MINUTE, HOUR, DAY)
            window_time_zone: Timezone for windowing

        Returns:
            UsageQueryResult containing the usage data
        """
        url = f"{self.base_url}/api/v1/meters/{meter_slug}/query"

        params = {
            "subject": subject,
            "windowSize": window_size,
            "windowTimeZone": window_time_zone,
        }

        if from_time:
            params["from"] = from_time
        if to_time:
            params["to"] = to_time

        # Apply rate limiting before making the API request
        self.checkout_rate_limiter.wait_if_needed()

        response = self.session.get(url, params=params)
        response.raise_for_status()

        response_data = response.json()
        return UsageQueryResult(
            data=response_data.get("data", []),
            from_=from_time,
            to=to_time,
            subject=subject,
            meter=meter_slug,
        )

    def get_customer_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a customer by key from OpenMeter.
        """
        url = f"{self.base_url}/api/v1/customers/{key}"
        response = self.session.get(url)
        if response.status_code == 404:
            logger.info(f"OpenMeter customer by key {key} not found")
            return None
        response.raise_for_status()
        return response.json()

    def list_customers(self, page: int = 1) -> Dict[str, Any]:
        """
        List all customers from OpenMeter.
        """
        url = f"{self.base_url}/api/v1/customers"
        response = self.session.get(url, params={"page": page})
        response.raise_for_status()
        return response.json()

    def list_subjects(self) -> Any:
        """
        List all subjects from OpenMeter.
        """
        url = f"{self.base_url}/api/v1/subjects"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def delete_customer(self, customer_id: str):
        """
        Delete a customer from OpenMeter.
        """
        url = f"{self.base_url}/api/v1/customers/{customer_id}"
        response = self.session.delete(url)
        response.raise_for_status()
        logger.info(f"Successfully deleted OpenMeter customer {customer_id}")

    def delete_subject(self, subject_id: str):
        """
        Delete a subject from OpenMeter.
        """
        url = f"{self.base_url}/api/v1/subjects/{subject_id}"
        response = self.session.delete(url)
        response.raise_for_status()

        logger.info(f"Successfully deleted OpenMeter subject {subject_id}")

    def find_customers_by_email(self, email: str) -> Dict[str, Any]:
        """
        Find customers by email from OpenMeter.
        """
        url = f"{self.base_url}/api/v1/customers"
        response = self.session.get(url, params={"primaryEmail": email})
        response.raise_for_status()
        return response.json()

    def find_customers_by_name(self, name: str) -> Dict[str, Any]:
        """
        Find customers by email from OpenMeter.
        """
        url = f"{self.base_url}/api/v1/customers"
        response = self.session.get(url, params={"name": name})
        response.raise_for_status()
        return response.json()

    def delete_all_customers(self):
        """
        Delete all customers from OpenMeter (only in dev environment)
        """
        if settings.environment != "development":
            logger.error(
                f"Not deleting all OpenMeter customers in non-development environment"
            )
            return

        customers = self.list_customers()
        for customer in customers["items"]:
            self.delete_customer(customer["id"])

        total_count = customers["totalCount"]
        page_size = customers["pageSize"]
        num_pages = total_count // page_size + 1
        for page in range(1, num_pages + 1):
            customers = self.list_customers(page)
            for customer in customers["items"]:
                self.delete_customer(customer["id"])

        logger.info(f"Successfully deleted all OpenMeter customers")

    def delete_all_subjects(self):
        """
        Delete all subjects from OpenMeter (only in dev environment)
        """
        if settings.environment != "development":
            logger.error(
                f"Not deleting all OpenMeter subjects in non-development environment"
            )
            return

        subjects = self.list_subjects()

        for subject in subjects:
            logger.info(f"deleting subject {subject['id']}")
            self.delete_subject(subject["id"])

        logger.info(f"Successfully deleted all OpenMeter subjects")
