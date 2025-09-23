import React from 'react';
import Modal from '#components/reusable/Modal';
import { Button, SecondaryButton } from '#components/reusable/Button';
import { XMarkIcon } from '@heroicons/react/24/outline';

/**
 * Props for the PaymentCancelledDialog component
 */
interface PaymentCancelledDialogProps {
    /**
     * Whether the dialog is currently open
     */
    isOpen: boolean;

    /**
     * Callback function when the dialog is closed
     */
    onClose: () => void;

    /**
     * Callback function to try payment again
     */
    onRetry: () => void;
}

/**
 * Dialog component for displaying payment cancelled message
 * @param {PaymentCancelledDialogProps} props - The component props
 * @returns {React.ReactElement} The payment cancelled dialog
 */
const PaymentCancelledDialog: React.FC<PaymentCancelledDialogProps> = ({ isOpen, onClose, onRetry }) => {
    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <div className="bg-background text-foreground rounded-lg p-6 max-w-md w-full mx-4 items-center">
                <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-yellow-100 rounded-full">
                    <XMarkIcon className="w-6 h-6 text-background" />
                </div>
                
                <div className="text-center">
                    <h3 className="text-lg font-semibold text-foreground mb-2">
                        Payment Cancelled
                    </h3>
                    <p className="text-sm text-foreground mb-6">
                        Your payment was cancelled and no money will be taken from your account. You can try again at any time.
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

export default PaymentCancelledDialog; 