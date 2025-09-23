import React, { useState } from 'react';
import { useBillingUsage } from '#hooks/useBillingUsage';
import {
    NewUserBillingView,
    BalanceHeader,
    SubscriptionDetails,
    TransactionHistory,
    PaymentErrorDialog,
    PaymentPendingDialog,
    PaymentCancelledDialog,
    RefundSection
} from '../components/billing';
import SubscriptionRequiredView from '#components/billing/SubscriptionRequiredView';
import PendingCancellationWarning from '#components/billing/PendingCancellationWarning';
import { UserAccountStatus } from '#constants/userAccountStatus';
import { useIsDeviceMobile } from '#hooks/isDeviceMobile';
import { cancelSubscriptionImmediately } from '#api/accounting';
import AppBackground from '#components/AppBackground';
import NavBar from '#components/reusable/NavBar';

/**
 * Billing & Usage page component for managing account credits and monitoring usage
 * @returns {React.ReactElement} The billing and usage page
 */
const BillingUsage: React.FC = () => {
    const {
        data,
        userAccountDetails,
        autoTopUp,
        setAutoTopUp,
        handleAddCredit,
        onboardCustomer,
        formatCurrency,
        isLoading,
        error,
        showErrorDialog,
        showPendingDialog,
        showCancelledDialog,
        closeErrorDialog,
        closePendingDialog,
        closeCancelledDialog,
        handlePaymentRetry,
        handlePaymentSuccess,
        handlePaymentFailure,
        handleRefundRequest,
        handleOpenCustomerPortal,
        loadTransactionsPage,
        resetTransactionsPagination
    } = useBillingUsage();

    const isMobile = useIsDeviceMobile();
    const [isCancellingImmediately, setIsCancellingImmediately] = useState(false);

    /**
     * Handle immediate subscription cancellation with refund
     */
    const handleCancelImmediately = async () => {
        try {
            setIsCancellingImmediately(true);

            const result = await cancelSubscriptionImmediately();

            if (result.success) {
                // Show success message and reload billing data
                console.log('Subscription canceled successfully:', result.message);
                // Reload the page to get updated account details
                window.location.reload();
            } else {
                console.error('Failed to cancel subscription:', result.message);
                // Could show an error dialog here
            }
        } catch (error) {
            console.error('Error canceling subscription:', error);
            // Could show an error dialog here
        } finally {
            setIsCancellingImmediately(false);
        }
    };


    // Show loading state
    if (isLoading) {
        return (
            <div className="min-h-screen bg-background text-foreground p-6 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                    <p className="text-muted-foreground">Loading billing information...</p>
                </div>
            </div>
        );
    }

    // Show error state
    if (error) {
        return (
            <div className="min-h-screen bg-background text-foreground p-6 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-destructive mb-4">Error loading billing information</p>
                    <p className="text-muted-foreground text-sm">{error.message}</p>
                </div>
            </div>
        );
    }

    // Show new user view if user is not onboarded
    if (userAccountDetails?.status == UserAccountStatus.NEW) {
        return (
            <AppBackground>
                <div className="inset-0 flex flex-col h-screen w-screen">
                    {/* Navigation bar */}
                    {!isMobile && <NavBar />}

                    {/* Carousel onboarding flow */}
                    <div className="flex-1 flex items-center justify-center">
                        <NewUserBillingView onboardCustomer={onboardCustomer} />
                    </div>
                </div>
            </AppBackground>
        );
    }

    // Show subscription required view for users without subscription or closed accounts
    if (userAccountDetails?.status === UserAccountStatus.NO_SUBSCRIPTION ||
        userAccountDetails?.status === UserAccountStatus.CLOSED) {
        return (
            <AppBackground>
                <div className="inset-0 flex flex-col h-screen w-screen">
                    {/* Navigation bar */}
                    {!isMobile && <NavBar />}

                    {/* Subscription required flow */}
                    <div className="flex-1 flex items-center justify-center">
                        <SubscriptionRequiredView subscriptionStatus={userAccountDetails.status} />
                    </div>
                </div>
            </AppBackground>
        );
    }

    const {
        currentBalance,
        transactions,
        transactionsPagination,
        subscriptionStatus,
        monthlyCreditsTotal,
        monthlyCreditsUsed
    } = data;

    // Conditional logic for showing BalanceHeader
    // Show when: usage balance > $0 OR monthly credits exhausted OR no active subscription
    const monthlyCreditsRemaining = Math.max(0, monthlyCreditsTotal - monthlyCreditsUsed);
    const hasActiveSubscription = subscriptionStatus === 'ACTIVE_SUBSCRIPTION';
    const hasUsageBalance = currentBalance > 0;
    const monthlyCreditsExhausted = monthlyCreditsRemaining <= 0;

    const shouldShowBalanceHeader = hasUsageBalance || monthlyCreditsExhausted || !hasActiveSubscription;

    return (
        <AppBackground>
            <div className="inset-0 flex flex-col h-screen w-screen">
                {/* Navigation bar */}
                {!isMobile && <NavBar />}

                {/* Main content */}
                <div className="flex-1 flex items-start justify-center overflow-y-auto">
                    <div className="min-h-screen py-10 text-foreground max-w-4xl w-full px-6">
                        <div className="flex flex-col gap-6">
                            {/* Pending Cancellation Warning - Show at top */}
                            {userAccountDetails?.subscriptionCancelAt && (
                                <PendingCancellationWarning
                                    userAccountDetails={userAccountDetails}
                                    onCancelImmediately={handleCancelImmediately}
                                    isProcessing={isCancellingImmediately}
                                />
                            )}

                            {/* Subscription Details - Primary priority */}
                            <SubscriptionDetails
                                subscriptionStatus={subscriptionStatus}
                                monthlyCreditsTotal={monthlyCreditsTotal}
                                monthlyCreditsUsed={monthlyCreditsUsed}
                                handleOpenCustomerPortal={handleOpenCustomerPortal}
                                formatCurrency={formatCurrency}
                            />

                            {/* Usage Balance - Show only when relevant */}
                            {shouldShowBalanceHeader && (
                                <BalanceHeader
                                    currentBalance={currentBalance}
                                    daysLeft={0}
                                    autoTopUp={autoTopUp}
                                    setAutoTopUp={setAutoTopUp}
                                    handleAddCredit={handleAddCredit}
                                    formatCurrency={formatCurrency}
                                />
                            )}

                            <TransactionHistory
                                transactions={transactions}
                                pagination={transactionsPagination}
                                formatCurrency={formatCurrency}
                                onPageChange={loadTransactionsPage}
                                onFirstPage={resetTransactionsPagination}
                            />

                            {hasUsageBalance && (
                                <RefundSection
                                    accountBalance={currentBalance}
                                    onRefundRequest={handleRefundRequest}
                                />
                            )}
                        </div>
                    </div>

                    {/* Payment Dialogs */}
                    <PaymentErrorDialog
                        isOpen={showErrorDialog}
                        onClose={closeErrorDialog}
                        onRetry={handlePaymentRetry}
                    />

                    <PaymentPendingDialog
                        isOpen={showPendingDialog}
                        onClose={closePendingDialog}
                        onSuccess={handlePaymentSuccess}
                        onFailure={handlePaymentFailure}
                    />

                    <PaymentCancelledDialog
                        isOpen={showCancelledDialog}
                        onClose={closeCancelledDialog}
                        onRetry={handlePaymentRetry}
                    />
                </div>
            </div>
        </AppBackground>
    );
};

export default BillingUsage; 