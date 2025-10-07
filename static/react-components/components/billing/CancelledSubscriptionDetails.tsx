import React from 'react';
import { MdWarning, MdSettings, MdCalendarToday, MdEmail } from 'react-icons/md';
import { UserAccountDetails } from '#api/accounting';

/**
 * Cancelled subscription details component
 * Shows subscription information with cancellation warning when user has cancelled
 * @param {object} props - Component props
 * @param {string} props.subscriptionStatus - Current subscription status
 * @param {number} props.monthlyCreditsTotal - Total monthly AI credits included (in cents)
 * @param {number} props.monthlyCreditsUsed - Monthly AI credits used this cycle (in cents)
 * @param {UserAccountDetails} props.userAccountDetails - User account details including cancellation date
 * @param {function} props.handleOpenCustomerPortal - Function to open Stripe customer portal
 * @param {function} props.formatCurrency - Function to format currency
 * @returns {React.ReactElement} The cancelled subscription details component
 */
const CancelledSubscriptionDetails: React.FC<{
    subscriptionStatus: string;
    monthlyCreditsTotal: number;
    monthlyCreditsUsed: number;
    userAccountDetails: UserAccountDetails;
    handleOpenCustomerPortal: () => Promise<void>;
    formatCurrency: (amount: number) => string;
}> = ({
    subscriptionStatus,
    monthlyCreditsTotal,
    monthlyCreditsUsed,
    userAccountDetails,
    handleOpenCustomerPortal,
    formatCurrency
}) => {
        const monthlyCreditsRemaining = Math.max(0, monthlyCreditsTotal - monthlyCreditsUsed);
        const creditsUsagePercentage = monthlyCreditsTotal > 0
            ? Math.min(100, (monthlyCreditsUsed / monthlyCreditsTotal) * 100)
            : 0;

        // Calculate cancellation details
        const cancelDate = userAccountDetails.subscriptionCancelAt
            ? new Date(userAccountDetails.subscriptionCancelAt)
            : null;
        const today = new Date();
        const daysUntilCancellation = cancelDate
            ? Math.ceil((cancelDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
            : 0;

        const formatDate = (date: Date) => {
            return date.toLocaleDateString('en-GB', {
                day: 'numeric',
                month: 'long',
                year: 'numeric'
            });
        };

        return (
            <div>
                <h2 className="text-xl font-semibold mb-4">Monthly Subscription</h2>

                <div className="border border-border rounded-lg p-6">
                    {/* Warning Header */}
                    <div className="flex items-start gap-3 mb-6 pb-6 border-b border-border">
                        <MdWarning className="text-destructive text-2xl mt-1 flex-shrink-0" />
                        <div className="flex-1">
                            <h3 className="text-lg font-semibold text-destructive mb-2">
                                Subscription Scheduled for Cancellation
                            </h3>
                            {cancelDate && (
                                <div className="flex items-center gap-2 text-sm text-foreground mb-3">
                                    <MdCalendarToday className="text-base" />
                                    <span>
                                        Your subscription will end on <strong>{formatDate(cancelDate)}</strong>
                                        {daysUntilCancellation > 0 && (
                                            <span> ({daysUntilCancellation} day{daysUntilCancellation !== 1 ? 's' : ''} remaining)</span>
                                        )}
                                    </span>
                                </div>
                            )}
                            <p className="text-sm text-muted-foreground">
                                You'll continue to have access to all subscription features until the end of your current billing period.
                                After that, your account will be downgraded and you'll lose access to AI features.
                            </p>
                        </div>
                    </div>

                    {/* Subscription Details */}
                    <div className="flex items-start justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-destructive/20 text-destructive">
                                <MdWarning className="text-lg" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold">
                                    Active Until Cancellation
                                </h3>
                                <p className="text-sm text-muted-foreground">
                                    $7/month - Includes AI credits + platform access
                                </p>
                            </div>
                        </div>

                        <button
                            onClick={handleOpenCustomerPortal}
                            className="flex items-center gap-2 px-3 py-2 text-sm bg-background border border-border rounded-lg hover:bg-muted transition-colors"
                        >
                            <MdSettings className="text-sm" />
                            Manage
                        </button>
                    </div>

                    {/* Monthly Credits Usage */}
                    <div className="mb-6">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">Monthly AI Credits</span>
                            <span className="text-sm text-muted-foreground">
                                {formatCurrency(monthlyCreditsUsed / 100)} / {formatCurrency(monthlyCreditsTotal / 100)} used
                            </span>
                        </div>

                        <div className="w-full bg-muted rounded-full h-2 mb-2">
                            <div
                                className={`h-2 rounded-full transition-all duration-300 ${creditsUsagePercentage >= 90
                                        ? 'bg-destructive'
                                        : creditsUsagePercentage >= 75
                                            ? 'bg-yellow-500'
                                            : 'bg-primary'
                                    }`}
                                style={{ width: `${creditsUsagePercentage}%` }}
                            />
                        </div>

                        <p className="text-xs text-muted-foreground">
                            {monthlyCreditsRemaining > 0
                                ? `${formatCurrency(monthlyCreditsRemaining / 100)} remaining this cycle`
                                : 'All monthly credits used - additional usage charged to balance'
                            }
                        </p>
                    </div>

                    {/* Refund Information */}
                    {/* <div className="bg-background/50 border border-border rounded-lg p-4">
                        <div className="flex items-start gap-3">
                            <MdEmail className="text-muted-foreground text-lg mt-0.5 flex-shrink-0" />
                            <div>
                                <h4 className="text-sm font-semibold mb-1">Need a Refund?</h4>
                                <p className="text-xs text-muted-foreground mb-2">
                                    To request a refund for your subscription, please contact our support team at{' '}
                                    <a
                                        href="mailto:support@openbacklog.ai"
                                        className="text-primary hover:underline"
                                    >
                                        support@openbacklog.ai
                                    </a>
                                </p>
                            </div>
                        </div>
                    </div> */}
                </div>
            </div>
        );
    };

export default CancelledSubscriptionDetails;
