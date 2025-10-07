import React, { useState } from 'react';
import { AddressElement, ExpressCheckoutElement, PaymentElement } from '@stripe/react-stripe-js';
import { PrimaryButton, SecondaryButton } from '#components/reusable/Button';
import { useSubscriptionPayment } from '#hooks/billing/useSubscriptionPayment';
import { usePaymentForm } from '#hooks/billing/usePaymentForm';
import {
  trackSubscriptionPaymentMethodSelected,
  trackSubscriptionCheckoutFormSubmitted,
} from '#services/tracking/onboarding';

/**
 * Props for the SubscriptionCheckout component
 */
interface SubscriptionCheckoutProps {
  onCancel: () => void;
  onSuccess: () => void;
  isLoading?: boolean;
}

/**
 * Custom subscription checkout component using Stripe Elements
 * Provides a branded payment experience with clear pricing and trust signals
 * @param {SubscriptionCheckoutProps} props - The component props
 * @returns {React.ReactElement} The subscription checkout component
 */
const SubscriptionCheckout: React.FC<SubscriptionCheckoutProps> = ({
  onCancel,
  onSuccess,
  isLoading = false
}) => {
  // State for manual form visibility
  const [showManualForm, setShowManualForm] = useState(false);

  // Use hooks for payment processing and form validation
  const {
    isProcessing,
    errorMessage,
    handleSubmit,
    handleExpressCheckout,
    clearError
  } = useSubscriptionPayment();
  
  const {
    cardComplete,
    addressComplete,
    acceptedTerms,
    expressCheckoutReady,
    isFormValid,
    setCardComplete,
    setAddressComplete,
    setAcceptedTerms,
    setExpressCheckoutReady,
    setCardError
  } = usePaymentForm();

  /**
   * Handle express checkout ready event
   */
  const handleExpressCheckoutReady = (event: any) => {
    // Check if any express payment methods are available
    const hasExpressOptions = event.availablePaymentMethods?.length > 0;
    setExpressCheckoutReady(hasExpressOptions);
    setShowManualForm(!hasExpressOptions); // Hide manual form if express options available
  };

  /**
   * Handle express checkout confirmation
   */
  const handleExpressCheckoutConfirm = async (event: any) => {
    // For express checkout, we still need terms to be accepted
    if (!acceptedTerms) {
      // Show terms requirement for express checkout
      setCardError('Please accept the terms and conditions to continue.');
      return;
    }

    // Track form submission with express payment method
    trackSubscriptionCheckoutFormSubmitted('express');

    try {
      // Process express payment using the payment hook
      await handleExpressCheckout(event);
      onSuccess();
    } catch (error) {
      console.error('Express checkout error:', error);
    }
  };

  /**
   * Toggle manual form visibility
   */
  const handleShowManualForm = () => {
    setShowManualForm(true);
    // Track payment method selection when user chooses manual form
    trackSubscriptionPaymentMethodSelected('manual');
  };

  /**
   * Handle manual form submission
   */
  const handleManualFormSubmit = async (event: any) => {
    // Track form submission with manual payment method
    trackSubscriptionCheckoutFormSubmitted('manual');

    // Call the original submit handler
    await handleSubmit(event);
  };

  // Form validity is handled by the usePaymentForm hook
  return (
    <div className="max-w-md mx-auto bg-card border border-border rounded-lg p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-foreground mb-2">Start Your Subscription</h1>
        <p className="text-muted-foreground">Join thousands of developers building better software</p>
      </div>

      {/* Plan Summary */}
      <div className="bg-primary/10 border border-primary/20 rounded-lg p-4">
        <div className="flex justify-between items-center mb-3">
          <span className="font-semibold text-foreground">Monthly Plan</span>
          <span className="text-2xl font-bold text-primary">£5/month</span>
        </div>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li className="flex items-center gap-2">
            <span className="text-primary">✓</span>
            Unlimited task management & MCP tools
          </li>
          <li className="flex items-center gap-2">
            <span className="text-primary">✓</span>
            Included AI credits to get started
          </li>
          <li className="flex items-center gap-2">
            <span className="text-primary">✓</span>
            Fair pay-as-you-go for additional AI usage
          </li>
          <li className="flex items-center gap-2">
            <span className="text-primary">✓</span>
            Cancel anytime - no commitment
          </li>
        </ul>
      </div>

      {/* Express Checkout */}
      <div className="space-y-4">
        <ExpressCheckoutElement
          onReady={handleExpressCheckoutReady}
          onConfirm={handleExpressCheckoutConfirm}
          options={{
            buttonType: {
              applePay: 'buy',
              googlePay: 'buy'
            },
            buttonHeight: 48,
            buttonTheme: {
              applePay: 'white-outline',
              googlePay: 'white'
            },
            layout: {
              maxColumns: 1,
              maxRows: 1,
            }
          }}
        />
      </div>

      {/* Terms & Conditions - Required for Express Checkout */}
      {expressCheckoutReady && (
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            id="express-terms"
            checked={acceptedTerms}
            onChange={(e) => setAcceptedTerms(e.target.checked)}
            className="mt-1 h-4 w-4 text-primary border-border rounded focus:ring-primary"
          />
          <label htmlFor="express-terms" className="text-sm text-muted-foreground">
            I agree to the{' '}
            <a href="https://www.openbacklog.ai/terms" target="_blank" className="text-primary hover:underline">
              Terms of Service
            </a>{' '}
            and{' '}
            <a href="https://www.openbacklog.ai/privacy" target="_blank" className="text-primary hover:underline">
              Privacy Policy
            </a>
          </label>
        </div>
      )}

      {/* Divider */}
      {expressCheckoutReady && (
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-border" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-card px-2 text-muted-foreground">
              {showManualForm ? 'Or pay with card' : 'Other payment methods'}
            </span>
          </div>
          {!showManualForm && (
            <div className="text-center mt-3">
              <button
                type="button"
                onClick={handleShowManualForm}
                className="text-sm text-primary hover:underline"
              >
                Pay with card instead
              </button>
            </div>
          )}
        </div>
      )}

      {/* Manual Payment Form - Show when no express checkout or user chooses manual */}
      {showManualForm && (
        <>
          {/* Customer Info */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">
                Customer Information
              </label>
              <div className="w-full bg-background border border-border rounded-md p-3 focus-within:ring-2 focus-within:ring-primary focus-within:border-primary">
                <AddressElement
                  options={{
                    mode: 'billing',
                  }}
                  onChange={(event) => {
                    setAddressComplete(event.complete);
                    if (event.complete) {
                      setCardError(null);
                    }
                  }}
                />
              </div>
            </div>
          </div>

          {/* Payment Form */}
          <form onSubmit={handleManualFormSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">
                Card Information
              </label>
              <div className="w-full px-3 py-3 bg-background border border-border rounded-md focus-within:ring-2 focus-within:ring-primary focus-within:border-primary">
                <PaymentElement
                  id="payment-element"
                  onChange={(event) => {
                    setCardComplete(event.complete)
                    if (event.complete) {
                      setCardError(null);
                    }
                  }}
                />
              </div>
            </div>

            {/* Terms & Conditions */}
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="terms"
                checked={acceptedTerms}
                onChange={(e) => setAcceptedTerms(e.target.checked)}
                className="mt-1 h-4 w-4 text-primary border-border rounded focus:ring-primary"
              />
              <label htmlFor="terms" className="text-sm text-muted-foreground">
                I agree to the{' '}
                <a href="https://www.openbacklog.ai/terms" target="_blank" className="text-primary hover:underline">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a href="https://www.openbacklog.ai/privacy" target="_blank" className="text-primary hover:underline">
                  Privacy Policy
                </a>
              </label>
            </div>

            {/* Submit Button */}
            <div className="pt-4">
              <PrimaryButton
                onClick={handleManualFormSubmit}
                disabled={!isFormValid || isProcessing}
                className="w-full"
              >
                {isProcessing ? 'Processing...' : 'Start Subscription'}
              </PrimaryButton>
            </div>

            {/* Trust Signals */}
            <div className="text-center pt-4 border-t border-border">
              <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground mb-2">
                <span className="inline-block w-4 h-4 bg-primary/20 rounded-full flex items-center justify-center">
                  <span className="text-primary font-bold text-xs">🔒</span>
                </span>
                Secure checkout powered by Stripe
              </div>
              <p className="text-xs text-muted-foreground">
                Cancel anytime • No setup fees • Developer-friendly pricing
              </p>
            </div>
          </form>
        </>
      )}

      {/* Error Message - Show for both express and manual checkout */}
      {errorMessage && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
          <p className="text-sm text-destructive">{errorMessage}</p>
        </div>
      )}

      {/* Cancel Button - Always visible */}
      <div className="flex justify-center pt-4">
        <SecondaryButton
          onClick={onCancel}
          disabled={isProcessing}
          className="px-8"
        >
          Cancel
        </SecondaryButton>
      </div>
    </div>
  );
};

export default SubscriptionCheckout;