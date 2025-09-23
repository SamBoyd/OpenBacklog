import React, { useState } from 'react';
import { MdWarning, MdCalendarToday, MdCancel } from 'react-icons/md';
import { UserAccountDetails } from '#api/accounting';

interface PendingCancellationWarningProps {
    userAccountDetails: UserAccountDetails;
    onCancelImmediately: () => void;
    isProcessing?: boolean;
}

/**
 * Warning component displayed when user has a pending subscription cancellation
 * Shows cancellation date and provides option to cancel immediately with refund
 */
const PendingCancellationWarning: React.FC<PendingCancellationWarningProps> = ({
    userAccountDetails,
    onCancelImmediately,
    isProcessing = false
}) => {
    const [showConfirmation, setShowConfirmation] = useState(false);

    // Don't render if no cancellation is scheduled
    if (!userAccountDetails.subscriptionCancelAt) {
        return null;
    }

    const cancelDate = new Date(userAccountDetails.subscriptionCancelAt);
    const today = new Date();
    const daysUntilCancellation = Math.ceil((cancelDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    const formatDate = (date: Date) => {
        return date.toLocaleDateString('en-GB', {
            day: 'numeric',
            month: 'long',
            year: 'numeric'
        });
    };

    const handleCancelImmediately = () => {
        setShowConfirmation(false);
        onCancelImmediately();
    };

    if (showConfirmation) {
        return (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-6 mb-6">
                <div className="flex items-start gap-4">
                    <MdWarning className="text-destructive text-xl mt-1 flex-shrink-0" />
                    <div className="flex-1">
                        <h3 className="text-lg font-semibold text-destructive mb-2">
                            Cancel Subscription Immediately?
                        </h3>
                        <p className="text-sm text-muted-foreground mb-4">
                            This will immediately cancel your subscription and process a full refund for your last payment. 
                            You will lose access to all subscription features right away instead of at the end of your billing period.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={handleCancelImmediately}
                                disabled={isProcessing}
                                className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg font-medium hover:bg-destructive/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isProcessing ? 'Processing...' : 'Yes, Cancel Now & Refund'}
                            </button>
                            <button
                                onClick={() => setShowConfirmation(false)}
                                disabled={isProcessing}
                                className="px-4 py-2 bg-muted text-muted-foreground rounded-lg font-medium hover:bg-muted/80 transition-colors disabled:opacity-50"
                            >
                                Keep Current Schedule
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-warning/10 border border-warning/20 rounded-lg p-6 mb-6">
            <div className="flex items-start gap-4">
                <MdWarning className="text-warning text-xl mt-1 flex-shrink-0" />
                <div className="flex-1">
                    <h3 className="text-lg font-semibold text-warning mb-2">
                        Subscription Scheduled for Cancellation
                    </h3>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                        <MdCalendarToday className="text-base" />
                        <span>
                            Your subscription will end on <strong>{formatDate(cancelDate)}</strong>
                            {daysUntilCancellation > 0 && (
                                <span> ({daysUntilCancellation} day{daysUntilCancellation !== 1 ? 's' : ''} remaining)</span>
                            )}
                        </span>
                    </div>
                    <p className="text-sm text-muted-foreground mb-4">
                        You'll continue to have access to all subscription features until the end of your current billing period.
                        After that, your account will be downgraded and you'll lose access to AI features.
                    </p>
                    <div className="flex justify-end">
                        <button
                            onClick={() => setShowConfirmation(true)}
                            disabled={isProcessing}
                            className="flex items-center gap-2 px-4 py-2 bg-destructive text-destructive-foreground rounded-lg font-medium hover:bg-destructive/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <MdCancel />
                            Cancel Now & Get Refund
                        </button>

                    </div>
                </div>
            </div>
        </div>
    );
};

export default PendingCancellationWarning;