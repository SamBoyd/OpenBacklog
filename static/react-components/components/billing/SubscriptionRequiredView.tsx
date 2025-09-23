import React from 'react';
import { MdSubscriptions, MdCheckCircle, MdInfo, MdWarning } from 'react-icons/md';
import { useNavigate } from 'react-router';
import { UserAccountStatus } from '#constants/userAccountStatus';

/**
 * Subscription required view for users who need to subscribe or reactivate
 * @param {object} props - Component props
 * @param {UserAccountStatus} props.subscriptionStatus - Current subscription status
 * @returns {React.ReactElement} The subscription required view component
 */
const SubscriptionRequiredView: React.FC<{
    subscriptionStatus: UserAccountStatus;
}> = ({ subscriptionStatus }) => {
    const navigate = useNavigate();

    const isClosedAccount = subscriptionStatus === UserAccountStatus.CLOSED;
    const isNoSubscription = subscriptionStatus === UserAccountStatus.NO_SUBSCRIPTION;

    /**
     * Handle navigation to subscription checkout
     */
    const handleSubscribe = () => {
        navigate('/workspace/billing/subscription/checkout');
    };

    const getTitle = () => {
        if (isClosedAccount) return 'Reactivate Your Account';
        if (isNoSubscription) return 'Subscription Required';
        return 'Subscription Required';
    };

    const getDescription = () => {
        if (isClosedAccount) {
            return 'Your account has been closed. Reactivate your subscription to continue using AI features and access your workspace.';
        }
        if (isNoSubscription) {
            return 'A monthly subscription is required to access the full platform. Subscribe now to unlock all AI features and workspace functionality.';
        }
        return 'A subscription is required to access this feature.';
    };

    const getButtonText = () => {
        if (isClosedAccount) return 'Reactivate Subscription';
        return 'Subscribe Now';
    };

    const getIcon = () => {
        if (isClosedAccount) return <MdWarning className="text-2xl" />;
        return <MdSubscriptions className="text-2xl" />;
    };

    return (
        <div className="min-h-screen bg-background text-foreground p-6 flex flex-col items-center justify-center">
            <div className="max-w-xl w-full space-y-8">
                <div className="bg-card border border-border rounded-lg p-8 text-center">
                    <h1 className="text-2xl font-bold mb-2">{getTitle()}</h1>
                    <p className="text-muted-foreground mb-4">
                        {getDescription()}
                    </p>
                    <div className="bg-muted rounded-lg p-4 mb-4">
                        <span className="block text-lg font-semibold mb-1">Monthly Subscription - £5/month</span>
                        <span className="text-sm text-muted-foreground">
                            Includes AI credits, full platform access, and premium features
                        </span>
                    </div>
                    <button
                        onClick={handleSubscribe}
                        className="mt-6 w-full flex items-center justify-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg text-lg font-semibold hover:bg-primary/90 transition-colors"
                    >
                        {getIcon()}
                        {getButtonText()}
                    </button>
                    <div className="mt-6 text-xs text-muted-foreground">
                        Cancel anytime. Full refunds available for unused credits.
                    </div>
                </div>

                {/* What's Included */}
                <div className="bg-card border border-border rounded-lg p-6">
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <MdCheckCircle className="text-success" /> What's Included
                    </h2>
                    <ul className="space-y-3">
                        <li className="flex items-center gap-3">
                            <MdCheckCircle className="text-success" />
                            <span>£5 worth of AI credits included every month</span>
                        </li>
                        <li className="flex items-center gap-3">
                            <MdCheckCircle className="text-success" />
                            <span>Full access to all workspace features</span>
                        </li>
                        <li className="flex items-center gap-3">
                            <MdCheckCircle className="text-success" />
                            <span>Priority support and updates</span>
                        </li>
                        <li className="flex items-center gap-3">
                            <MdCheckCircle className="text-success" />
                            <span>Additional usage charged to your balance</span>
                        </li>
                    </ul>
                </div>

                {/* Additional Information */}
                <div className="bg-card border border-border rounded-lg p-6">
                    <h3 className="text-lg text-muted-foreground font-semibold mb-3 flex items-center gap-2">
                        <MdInfo className="text-blue-500" /> How It Works
                    </h3>
                    <ul className="list-disc pl-5 text-sm space-y-2">
                        <li>£5/month subscription includes platform access and AI credits</li>
                        <li>When monthly credits are used up, additional usage comes from your balance</li>
                        <li>Top up your balance anytime for extra AI usage</li>
                        <li>Cancel your subscription anytime - unused credits remain available</li>
                        <li>Request full refunds for your remaining balance with one click</li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default SubscriptionRequiredView;