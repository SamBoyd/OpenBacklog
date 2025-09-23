import React, { useEffect, useState } from 'react';
import { useBillingUsage } from '#hooks/useBillingUsage';
import { useNavigate } from 'react-router';

interface ChatErrorViewProps {
    error: string | null;
}

/**
 * A component that displays error messages with animation and billing prompts for free tier limits
 * @param {ChatErrorViewProps} props - Component props
 * @param {string | null} props.error - The error message to display
 * @returns {React.ReactElement} The error view component
 */
const ChatErrorView: React.FC<ChatErrorViewProps> = ({ error }) => {    
    const [isVisible, setIsVisible] = useState(true);
    const [isDismissed, setIsDismissed] = useState(false);
    const navigate = useNavigate();

    // Reset visibility when error changes
    useEffect(() => {
        if (error) {
            setIsVisible(true);
            setIsDismissed(false);
        }
    }, [error]);

    // Auto-hide non-billing errors after 5 seconds
    useEffect(() => {
        if (!error || isBillingError(error)) return;

        const timeout = setTimeout(() => {
            setIsVisible(false);
        }, 5000);
        return () => clearTimeout(timeout);
    }, [error]);

    const isBillingError = (errorMessage: string): boolean => {
        return errorMessage.includes('Insufficient balance')
    };

    const handleAddFunds = () => {
        navigate('/workspace/billing')
    };

    const handleDismiss = () => {
        setIsDismissed(true);
        setIsVisible(false);
    };

    if (!error || isDismissed) return <></>;

    const isBilling = isBillingError(error);

    return (
        <div className={`${isVisible ? 'block' : 'hidden'}`}>
            <div className={`m-2 p-3 rounded-lg border ${
                isBilling 
                    ? 'border-amber-200 bg-amber-50 text-amber-800' 
                    : 'border-destructive/20 bg-destructive/5 text-destructive'
            }`}>
                {isBilling ? (
                    <>
                        <div className="flex items-start justify-between gap-3">
                            <div className="flex-1">
                                <p className="text-xs text-amber-700 mb-3">
                                    {error}
                                </p>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={handleAddFunds}
                                        className="px-3 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors"
                                    >
                                        Add Funds
                                    </button>
                                    <button
                                        onClick={handleDismiss}
                                        className="px-2 py-1 text-xs text-amber-600 hover:text-amber-800 transition-colors"
                                    >
                                        Dismiss
                                    </button>
                                </div>
                            </div>
                            <button
                                onClick={handleDismiss}
                                className="text-amber-600 hover:text-amber-800 text-lg leading-none"
                            >
                                ×
                            </button>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="flex items-start justify-between gap-3">
                            <div className="flex-1">
                                <p className="text-xs font-medium mb-1">
                                    An error occurred while processing your request.
                                </p>
                                <p className="text-xs text-destructive/90">
                                    If the problem persists, please contact support.
                                </p>
                            </div>
                            <button
                                onClick={handleDismiss}
                                className="text-destructive/60 hover:text-destructive text-lg leading-none"
                            >
                                ×
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default ChatErrorView;
