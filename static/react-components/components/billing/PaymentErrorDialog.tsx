import React from 'react';
import Modal from '#components/reusable/Modal';
import { Button, SecondaryButton } from '#components/reusable/Button';
import { XCircleIcon } from '@heroicons/react/24/outline';

/**
 * Props for the PaymentErrorDialog component
 */
interface PaymentErrorDialogProps {
    /**
     * Whether the dialog is currently open
     */
    isOpen: boolean;

    /**
     * Callback function when the dialog is closed
     */
    onClose: () => void;

    /**
     * Callback function to retry the payment
     */
    onRetry: () => void;
}

/**
 * Dialog component for displaying payment error messages
 * @param {PaymentErrorDialogProps} props - The component props
 * @returns {React.ReactElement} The payment error dialog
 */
const PaymentErrorDialog: React.FC<PaymentErrorDialogProps> = ({ isOpen, onClose, onRetry }) => {
    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <div className="bg-background text-foreground rounded-lg p-6 max-w-md w-full mx-4">
                <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-red-100 rounded-full">
                    <XCircleIcon className="w-6 h-6 text-red-600" />
                </div>
                
                <div className="text-center">
                    <h3 className="text-lg font-semibold text-foreground mb-2">
                        Payment Error
                    </h3>
                    <p className="text-sm text-foreground mb-6">
                        There was an issue processing your payment. Please try again or contact support if the problem persists.
                    </p>
                    
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <SecondaryButton
                            onClick={onRetry}
                        >
                            Try Again
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

export default PaymentErrorDialog; 