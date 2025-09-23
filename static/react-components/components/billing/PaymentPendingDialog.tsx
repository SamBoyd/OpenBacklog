import React, { useEffect, useState } from 'react';
import Modal from '#components/reusable/Modal';
import { Button, SecondaryButton } from '#components/reusable/Button';
import { ClockIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { getPendingTopupStatus, PendingTopupStatus } from '#api/accounting';

/**
 * Props for the PaymentPendingDialog component
 */
interface PaymentPendingDialogProps {
    /**
     * Whether the dialog is currently open
     */
    isOpen: boolean;

    /**
     * Callback function when the dialog is closed
     */
    onClose: () => void;

    /**
     * Callback function when payment is completed successfully
     */
    onSuccess: () => void;

    /**
     * Callback function when payment fails
     */
    onFailure: () => void;
}

/**
 * Dialog component for displaying payment pending status
 * @param {PaymentPendingDialogProps} props - The component props
 * @returns {React.ReactElement} The payment pending dialog
 */
const PaymentPendingDialog: React.FC<PaymentPendingDialogProps> = ({ 
    isOpen, 
    onClose, 
    onSuccess, 
    onFailure 
}) => {
    const [pendingStatus, setPendingStatus] = useState<PendingTopupStatus | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    /**
     * Fetches the current pending topup status
     */
    const fetchPendingStatus = async () => {
        try {
            setIsLoading(true);
            setError(null);
            const status = await getPendingTopupStatus();
            setPendingStatus(status);
            
            if (status) {
                if (status.status === 'COMPLETED') {
                    onSuccess();
                } else if (status.status === 'FAILED' || status.status === 'CANCELLED') {
                    onFailure();
                }
            }
        } catch (err) {
            setError('Failed to check payment status');
            console.error('Error fetching pending status:', err);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (isOpen) {
            fetchPendingStatus();
            
            const interval = setInterval(fetchPendingStatus, 5000);
            return () => clearInterval(interval);
        }
        return () => {}
    }, [isOpen]);

    const getStatusIcon = () => {
        if (isLoading) {
            return <ClockIcon className="w-6 h-6 text-blue-600 animate-spin" />;
        }
        
        if (pendingStatus?.status === 'COMPLETED') {
            return <CheckCircleIcon className="w-6 h-6 text-green-600" />;
        }
        
        if (pendingStatus?.status === 'FAILED' || pendingStatus?.status === 'CANCELLED') {
            return <XCircleIcon className="w-6 h-6 text-red-600" />;
        }
        
        return <ClockIcon className="w-6 h-6 text-blue-600" />;
    };

    const getStatusMessage = () => {
        if (isLoading) {
            return 'Checking payment status...';
        }
        
        if (error) {
            return 'Unable to check payment status. Please refresh the page.';
        }
        
        if (!pendingStatus) {
            return 'No pending payment found.';
        }
        
        switch (pendingStatus.status) {
            case 'PENDING':
                return 'Your payment is being processed. This may take a few minutes.';
            case 'COMPLETED':
                return 'Payment completed successfully!';
            case 'FAILED':
                return 'Payment failed. Please try again.';
            case 'CANCELLED':
                return 'Payment was cancelled.';
            default:
                return 'Payment status unknown.';
        }
    };

    const getStatusColor = () => {
        if (isLoading || pendingStatus?.status === 'PENDING') {
            return 'text-blue-600';
        }
        
        if (pendingStatus?.status === 'COMPLETED') {
            return 'text-green-600';
        }
        
        if (pendingStatus?.status === 'FAILED' || pendingStatus?.status === 'CANCELLED') {
            return 'text-red-600';
        }
        
        return 'text-gray-600';
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <div className="bg-background text-foreground rounded-lg p-6 max-w-md w-full mx-4">
                <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-blue-100 rounded-full">
                    {getStatusIcon()}
                </div>
                
                <div className="text-center">
                    <h3 className="text-lg font-semibold text-foreground mb-2">
                        Payment Processing
                    </h3>
                    <p className={`text-sm ${getStatusColor()} mb-6`}>
                        {getStatusMessage()}
                    </p>
                    
                    {pendingStatus && (
                        <div className="bg-background text-foreground rounded-lg p-4 mb-6">
                            <div className="text-sm text-foreground">
                                <div className="flex justify-between mb-1">
                                    <span>Amount:</span>
                                    <span className="font-medium">
                                        ${(pendingStatus.amountCents / 100).toFixed(2)}
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Status:</span>
                                    <span className="font-medium capitalize">
                                        {pendingStatus.status.toLowerCase()}
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                    
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <SecondaryButton
                            onClick={fetchPendingStatus}
                            disabled={isLoading}
                        >
                            {isLoading ? 'Checking...' : 'Refresh Status'}
                        </SecondaryButton>
                        <Button
                            onClick={onClose}
                            className="flex-1"
                        >
                            Close
                        </Button>
                    </div>
                </div>
            </div>
        </Modal>
    );
};

export default PaymentPendingDialog; 