from src.accounting.models import UserAccountStatus

billing_fsm_transitions = [
    # Subscription lifecycle
    {
        "trigger": "do_signup_subscription",
        "source": UserAccountStatus.NEW,
        "dest": UserAccountStatus.ACTIVE_SUBSCRIPTION,
    },
    {
        "trigger": "do_signup_subscription",
        "source": UserAccountStatus.NO_SUBSCRIPTION,
        "dest": UserAccountStatus.ACTIVE_SUBSCRIPTION,
    },
    {
        "trigger": "do_skip_subscription",
        "source": UserAccountStatus.NEW,
        "dest": UserAccountStatus.NO_SUBSCRIPTION,
    },
    {
        "trigger": "do_cancel_subscription",
        "source": UserAccountStatus.ACTIVE_SUBSCRIPTION,
        "dest": UserAccountStatus.NO_SUBSCRIPTION,
    },
    {
        "trigger": "do_cancel_subscription",
        "source": UserAccountStatus.SUSPENDED,
        "dest": UserAccountStatus.NO_SUBSCRIPTION,
    },
    # Usage recording transitions
    {
        "trigger": "usage_recorded",
        "source": UserAccountStatus.ACTIVE_SUBSCRIPTION,
        "dest": UserAccountStatus.METERED_BILLING,
        "conditions": "has_usage_balance",
    },
    {
        "trigger": "usage_recorded",
        "source": UserAccountStatus.ACTIVE_SUBSCRIPTION,
        "dest": UserAccountStatus.SUSPENDED,
        "conditions": "has_zero_usage_balance",
    },
    {
        "trigger": "usage_recorded",
        "source": UserAccountStatus.METERED_BILLING,
        "dest": UserAccountStatus.METERED_BILLING,
        "conditions": "has_usage_balance",
    },
    {
        "trigger": "usage_recorded",
        "source": UserAccountStatus.METERED_BILLING,
        "dest": UserAccountStatus.SUSPENDED,
        "conditions": "has_zero_usage_balance",
    },
    {
        "trigger": "usage_recorded",
        "source": UserAccountStatus.SUSPENDED,
        "dest": UserAccountStatus.SUSPENDED,
    },
    # Top-up transitions
    {
        "trigger": "topup_balance",
        "source": UserAccountStatus.ACTIVE_SUBSCRIPTION,
        "dest": UserAccountStatus.ACTIVE_SUBSCRIPTION,
    },
    {
        "trigger": "topup_balance",
        "source": UserAccountStatus.METERED_BILLING,
        "dest": UserAccountStatus.METERED_BILLING,
    },
    {
        "trigger": "topup_balance",
        "source": UserAccountStatus.SUSPENDED,
        "dest": UserAccountStatus.METERED_BILLING,
    },
    # Billing cycle reset
    {
        "trigger": "start_billing_cycle",
        "source": UserAccountStatus.ACTIVE_SUBSCRIPTION,
        "dest": UserAccountStatus.ACTIVE_SUBSCRIPTION,
    },
    {
        "trigger": "start_billing_cycle",
        "source": UserAccountStatus.METERED_BILLING,
        "dest": UserAccountStatus.ACTIVE_SUBSCRIPTION,
    },
    {
        "trigger": "start_billing_cycle",
        "source": UserAccountStatus.SUSPENDED,
        "dest": UserAccountStatus.ACTIVE_SUBSCRIPTION,
    },
    # Refund transitions
    {
        "trigger": "refund_balance",
        "source": UserAccountStatus.METERED_BILLING,
        "dest": UserAccountStatus.SUSPENDED,
    },
    {
        "trigger": "refund_balance",
        "source": UserAccountStatus.ACTIVE_SUBSCRIPTION,
        "dest": UserAccountStatus.ACTIVE_SUBSCRIPTION,
    },
    # Chargeback transitions (one-way to Closed)
    {
        "trigger": "chargeback_detected",
        "source": "*",
        "dest": UserAccountStatus.CLOSED,
    },
]
