import React, { useState } from 'react';
import type { RefundResult } from '#api/accounting';
import { Button, SecondaryButton } from '#components/reusable/Button';
import Modal from '#components/reusable/Modal';

interface RefundSectionProps {
    accountBalance: number;
    onRefundRequest: () => Promise<RefundResult>;
}

const RefundSection: React.FC<RefundSectionProps> = ({ accountBalance, onRefundRequest }: RefundSectionProps) => {
    const [showConfirmModal, setShowConfirmModal] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const handleRefundClick = () => {
        setShowConfirmModal(true);
    };

    const handleConfirmRefund = async () => {
        setShowConfirmModal(false);
        const result = await onRefundRequest();
        if (!result.success) {
            setErrorMessage(result.details ?? 'Refund failed. Please try again.');
        }
    };

    const handleCancelRefund = () => {
        setShowConfirmModal(false);
    };

    return (
        <>
            <div className="bg-card border border-border rounded-lg p-4">
                <h3 className="text-lg text-muted-foreground font-semibold mb-3">Refunds</h3>
                <div className="flex flex-row justify-around items-start">
                    <div className="text-sm text-muted-foreground">
                        <div>Get your remaining account balance refunded instantly.</div>
                        <div>No fees. No questions. No fuss. One click and you're done.</div>
                    </div>

                    <div className="self-end">
                        <Button
                            onClick={handleRefundClick}
                            disabled={accountBalance <= 0}
                        >
                            Refund ${accountBalance.toFixed(2)}
                        </Button>
                    </div>
                </div>

                {errorMessage && (
                    <div className="mt-4 p-3 border border-destructive text-destructive rounded-md bg-destructive/10">
                        {errorMessage}
                    </div>
                )}
            </div>

            <Modal isOpen={showConfirmModal} onClose={handleCancelRefund}>
                <div className="border border-border bg-background text-foreground rounded-lg p-6 max-w-md">
                    <h3 className="text-lg font-semibold mb-4 mx-auto">Confirm Refund</h3>

                    <div className="space-y-4 text-sm text-muted-foreground">
                        <p>
                            We'll refund your remaining account balance to your original payment method.
                        </p>

                        <p>
                            <strong>Important:</strong> This refunds only your remaining balance, not the total amount you've ever credited to your account. If you have recent usage, it will be deducted from your refund.
                        </p>

                        <p>
                            Refunds typically take <strong>3-5 business days</strong> to appear in your account, depending on your bank's processing time.
                        </p>
                    </div>

                    <div className="flex gap-3 mt-6">
                        <SecondaryButton
                            onClick={handleCancelRefund}
                            className="flex-1"
                        >
                            Cancel
                        </SecondaryButton>
                        <Button
                            onClick={handleConfirmRefund}
                            className="flex-1"
                        >
                            Confirm Refund
                        </Button>
                    </div>
                </div>
            </Modal>
        </>
    );
};

export default RefundSection;