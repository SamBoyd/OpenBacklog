import React, { useEffect } from 'react';
import { MdCheckCircle, MdInfo, MdClose } from 'react-icons/md';
import { useNavigate } from 'react-router';
import { UserAccountStatus } from '#constants/userAccountStatus';
import {
    trackFreeUserSubscriptionPromptViewed,
    trackFreeUserSubscriptionCTAClicked,
} from '#services/tracking/onboarding';

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

    // Track when subscription prompt is viewed
    useEffect(() => {
        trackFreeUserSubscriptionPromptViewed('billing_page', subscriptionStatus);
    }, [subscriptionStatus]);

    /**
     * Handle navigation to subscription checkout
     */
    const handleSubscribe = () => {
        const action = isClosedAccount ? 'reactivate_subscription' : 'unlock_ai_features';
        trackFreeUserSubscriptionCTAClicked('billing_page', action);
        navigate('/workspace/billing/subscription/checkout');
    };

    const getTitle = () => {
        if (isClosedAccount) return 'Reactivate Your Account';
        if (isNoSubscription) return 'Ready to Build Faster?';
        return 'Ready to Build Faster?';
    };

    const getDescription = () => {
        if (isClosedAccount) {
            return 'Your account has been closed. Reactivate your subscription to continue using AI features and access your workspace.';
        }
        if (isNoSubscription) {
            return "You've been using OpenBacklog to manage your tasks—nice work. Now unlock AI features to ship even faster. Get intelligent task breakdowns, automated planning, and smart suggestions that keep you in flow.";
        }
        return "You've been using OpenBacklog to manage your tasks—nice work. Now unlock AI features to ship even faster.";
    };

    const getButtonText = () => {
        if (isClosedAccount) return 'Reactivate subscription';
        return 'Subscribe now';
    };



    return (
        <div className="min-h-screen text-foreground py-16 flex flex-col items-center justify-center">
            <div className="max-w-5xl w-full space-y-16">
                <div className="text-center">
                    <h1 className="text-2xl font-bold mb-2">{getTitle()}</h1>
                    <p className="text-muted-foreground">{getDescription()}</p>
                </div>

                {/* Plans comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                    {/* Free Plan */}
                    <div className="bg-card border border-border rounded-lg">
                        <div className="flex flex-col items-start justify-between px-6 py-10 bg-gradient-to-r from-primary/10 to-transparent rounded-md">
                            <h2 className="text-xl font-semibold">Free plan</h2>
                        </div>

                        <div className=" p-6 flex flex-col space-y-10">
                            <div className="py-3">
                                <span className="text-8xl">$0</span>
                                <span className="text-muted-foreground ml-2">per month</span>
                            </div>


                            <ul className="mt-4 space-y-3 flex-1">
                                <div className="text-muted-foreground text-sm">Great for getting started</div>

                                <li className="flex items-center gap-3">
                                    <MdCheckCircle className="text-success" />
                                    <span>Unlimited projects and tasks</span>
                                </li>
                                <li className="flex items-center gap-3">
                                    <MdCheckCircle className="text-success" />
                                    <span>Manual planning tools and checklists</span>
                                </li>
                                <li className="flex items-center gap-3">
                                    <MdCheckCircle className="text-success" />
                                    <span>Email support</span>
                                </li>
                                <li className="flex items-center gap-3 text-muted-foreground">
                                    <MdClose />
                                    <span>No AI task breakdowns or smart suggestions</span>
                                </li>
                                <li className="flex items-center gap-3 text-muted-foreground">
                                    <MdClose />
                                    <span>No included AI credits</span>
                                </li>
                            </ul>

                            <div className="w-full flex flex-col items-center">

                                <button
                                    onClick={() => {}}
                                    className="mt-6 mb-6 w-full px-6 h-10 border border-border rounded-lg font-medium cursor-default"
                                >
                                    Current plan
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Paid Plan */}
                    <div className="bg-card border border-border rounded-lg ring-1 ring-primary/20">
                        <div className="flex flex-col items-start justify-between px-6 py-10 bg-gradient-to-r from-primary/20 to-transparent rounded-md">
                            <h2 className="text-xl font-semibold">Monthly Subscription</h2>
                        </div>

                        <div className="p-6 flex flex-col space-y-10">

                            <div className="py-3">
                                <span className="text-8xl">$7</span>
                                <span className="text-muted-foreground ml-2">per month</span>
                            </div>

                            <ul className="mt-4 space-y-3 flex-1">
                                <div className="text-muted-foreground text-sm">Unlock AI features</div>
                                <li className="flex items-center gap-3">
                                    <MdCheckCircle className="text-success" />
                                    <span>AI-powered task planning and breakdowns</span>
                                </li>
                                <li className="flex items-center gap-3">
                                    <MdCheckCircle className="text-success" />
                                    <span>Intelligent suggestions that keep you in flow</span>
                                </li>
                                <li className="flex items-center gap-3">
                                    <MdCheckCircle className="text-success" />
                                    <span>Best-practice guidance while you build</span>
                                </li>
                                <li className="flex items-center gap-3">
                                    <MdCheckCircle className="text-success" />
                                    <span>$7 in AI credits included monthly — top up anytime</span>
                                </li>
                                <li className="flex items-center gap-3">
                                    <MdCheckCircle className="text-success" />
                                    <span>Priority support</span>
                                </li>
                            </ul>

                            <div className="w-full flex flex-col items-center">
                                <button
                                    onClick={handleSubscribe}
                                    className={
                                        "mt-6 w-full flex items-center justify-center gap-2 px-6 h-10 bg-primary " +
                                        "text-primary-foreground rounded-lg text-md font-semibold hover:bg-primary/90 transition-colors"
                                    }
                                >
                                    {getButtonText()}
                                </button>
                                <div className="h-3 mt-3 text-xs text-muted-foreground text-center">
                                    Cancel anytime. Full refunds for unused balance.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Additional Information */}
                <div className="bg-card border border-border rounded-lg p-6">
                    <h3 className="text-lg text-muted-foreground font-semibold mb-3 flex items-center gap-2">
                        <MdInfo className="text-blue-500" /> How It Works
                    </h3>
                    <ul className="list-disc pl-5 text-sm space-y-2">
                        <li>$7/month subscription includes platform access and AI credits</li>
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