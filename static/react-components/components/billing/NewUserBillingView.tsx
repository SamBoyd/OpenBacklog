import React from 'react';
import { MdCreditCard, MdPlayArrow, MdCheckCircle, MdInfo } from 'react-icons/md';

/**
 * New user onboarding view for billing
 * @param {object} props - Component props
 * @param {() => void} props.onboardCustomer - Function to onboard the customer
 * @returns {React.ReactElement} The new user billing view component
 */
const NewUserBillingView: React.FC<{
    onboardCustomer: () => void;
}> = ({ onboardCustomer }) => (
    <div className="min-h-screen bg-background text-foreground p-6 flex flex-col items-center justify-center">
        <div className="max-w-xl w-full space-y-8">
            <div className="bg-card border border-border rounded-lg p-8 text-center">
                <h1 className="text-2xl font-bold mb-2">Welcome to Billing & Usage</h1>
                <p className="text-muted-foreground mb-4">
                    Top up your account to unlock all AI features. Your balance is <span className="font-semibold text-primary">100% refundable at any time</span>—no questions asked.
                </p>
                <div className="bg-muted rounded-lg p-4 mb-4">
                    <span className="block text-lg font-semibold mb-1">One-Click Refunds</span>
                    <span className="text-sm text-muted-foreground">
                        Changed your mind? You can request a full refund of your remaining balance instantly, right from your dashboard.
                    </span>
                </div>
                <button
                    onClick={onboardCustomer}
                    className="mt-6 w-full flex items-center justify-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg text-lg font-semibold hover:bg-primary/90 transition-colors"
                >
                    <MdCreditCard className="text-2xl" />
                    Get Started – Add Credit
                </button>
                <div className="mt-6 text-xs text-muted-foreground">
                    No monthly minimums. Pay only for what you use. Cancel and refund anytime.
                </div>
            </div>

            {/* Getting Started Checklist */}
            <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <MdPlayArrow className="text-primary" /> Getting Started
                </h2>
                <ul className="space-y-3">
                    <li className="flex items-center gap-3">
                        <MdCheckCircle className="text-green-500" />
                        <span>Sign up for your account</span>
                    </li>
                    <li className="flex items-center gap-3">
                        <MdCreditCard className="text-primary" />
                        <span>Add your first credit to unlock AI features</span>
                    </li>
                    <li className="flex items-center gap-3">
                        <MdInfo className="text-blue-500" />
                        <span>Explore the dashboard and try out your first AI-powered task</span>
                    </li>
                </ul>
            </div>

            {/* How Billing Works */}
            <div className="bg-card border border-border rounded-lg p-6">
                <h3 className="text-lg text-muted-foreground font-semibold mb-3">How Billing Works</h3>
                <ul className="list-disc pl-5 text-sm space-y-2">
                    <li>Pay only for what you use – no monthly minimums.</li>
                    <li>Top up your account to access AI features.</li>
                    <li>Track your usage and spending in real time.</li>
                    <li>Download receipts for your records.</li>
                    <li>Request full refunds anytime with one click.</li>
                </ul>
            </div>
        </div>
    </div>
);

export default NewUserBillingView; 