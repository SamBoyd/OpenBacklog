import { useState } from 'react';
import { useCheckout } from '@stripe/react-stripe-js';

/**
 * Interface for the subscription payment hook return value
 */
export interface UseSubscriptionPaymentReturn {
  isProcessing: boolean;
  errorMessage: string | null;
  handleSubmit: (event: any) => Promise<void>;
  handleExpressCheckout: (event: any) => Promise<void>;
  clearError: () => void;
}

/**
 * Hook for managing subscription payment processing with Stripe
 * Handles payment method creation, setup intent confirmation, and error states
 * @returns {UseSubscriptionPaymentReturn} Payment processing state and handlers
 */
export const useSubscriptionPayment = (): UseSubscriptionPaymentReturn => {
  const checkout = useCheckout();

  
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  /**
   * Clear any existing error messages
   */
  const clearError = () => {
    setErrorMessage(null);
  };
  
  const handleSubmit = async (event: any) => {
    // We don't want to let default form submission happen here,
    // which would refresh the page.
    event.preventDefault();
    setIsProcessing(true)

    const result = await checkout.confirm();

    
    if (result.type === 'error') {
      setIsProcessing(false)
      setErrorMessage(result.error.message)
      // Show error to your customer (for example, payment details incomplete)
      console.log(result.error.message);
    } else {
      // Your customer will be redirected to your `return_url`. For some payment
      // methods like iDEAL, your customer will be redirected to an intermediate
      // site first to authorize the payment, then redirected to the `return_url`.

    }
  };

  return {
    isProcessing,
    errorMessage,
    handleSubmit,
    handleExpressCheckout: (event: any) => Promise.resolve(),
    clearError,
  };
};