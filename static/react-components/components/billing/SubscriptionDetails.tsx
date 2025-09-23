import { UserAccountStatus } from '#constants/userAccountStatus';
import React from 'react';
import { MdCheck, MdCreditCard, MdSettings } from 'react-icons/md';

/**
 * Subscription details component displaying monthly subscription information
 * @param {object} props - Component props
 * @param {string} props.subscriptionStatus - Current subscription status
 * @param {number} props.monthlyCreditsTotal - Total monthly AI credits included (in cents)
 * @param {number} props.monthlyCreditsUsed - Monthly AI credits used this cycle (in cents)
 * @param {function} props.handleOpenCustomerPortal - Function to open Stripe customer portal
 * @param {function} props.formatCurrency - Function to format currency
 * @returns {React.ReactElement} The subscription details component
 */
const SubscriptionDetails: React.FC<{
    subscriptionStatus: string;
    monthlyCreditsTotal: number;
    monthlyCreditsUsed: number;
    handleOpenCustomerPortal: () => Promise<void>;
    formatCurrency: (amount: number) => string;
}> = ({
    subscriptionStatus,
    monthlyCreditsTotal,
    monthlyCreditsUsed,
    handleOpenCustomerPortal,
    formatCurrency
}) => {
        const monthlyCreditsRemaining = Math.max(0, monthlyCreditsTotal - monthlyCreditsUsed);
        const creditsUsagePercentage = monthlyCreditsTotal > 0
            ? Math.min(100, (monthlyCreditsUsed / monthlyCreditsTotal) * 100)
            : 0;

        return (
            <div>
                <h2 className="text-xl font-semibold mb-4">Monthly Subscription</h2>

                <div className="bg-card border border-border rounded-lg p-6">
                    <div className="flex items-start justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className={`
                            flex items-center justify-center w-10 h-10 rounded-full
                            bg-success/20 text-success
                        `}>
                                <MdCheck className="text-lg" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold">
                                    Active Subscription
                                </h3>
                                <p className="text-sm text-muted-foreground">
                                    £5/month - Includes AI credits + platform access
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
                </div>
            </div>
        );
    };

export default SubscriptionDetails;