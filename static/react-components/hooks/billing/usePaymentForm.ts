import { useState } from 'react';
import { useStripe } from '@stripe/react-stripe-js';

/**
 * Interface for the payment form hook return value
 */
export interface UsePaymentFormReturn {
  cardComplete: boolean;
  addressComplete: boolean;
  acceptedTerms: boolean;
  expressCheckoutReady: boolean;
  isFormValid: boolean;
  setCardComplete: (complete: boolean) => void;
  setAddressComplete: (complete: boolean) => void;
  setAcceptedTerms: (accepted: boolean) => void;
  setExpressCheckoutReady: (ready: boolean) => void;
  setCardError: (error: string | null) => void;
  validateForm: () => boolean;
}

/**
 * Hook for managing payment form validation and state
 * Handles card completion, terms acceptance, and overall form validity
 * @returns {UsePaymentFormReturn} Form validation state and handlers
 */
export const usePaymentForm = (): UsePaymentFormReturn => {
  const stripe = useStripe();
  
  const [cardComplete, setCardComplete] = useState(false);
  const [addressComplete, setAddressComplete] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [expressCheckoutReady, setExpressCheckoutReady] = useState(false);
  const [cardError, setCardError] = useState<string | null>(null);

  /**
   * Calculate if the form is valid and ready for submission
   * @returns {boolean} True if form is valid
   */
  const isFormValid = Boolean(
    stripe && 
    acceptedTerms && 
    !cardError &&
    (
      // Either express checkout is ready, or manual form is complete
      expressCheckoutReady || 
      (cardComplete && addressComplete)
    )
  );

  /**
   * Validate the entire form
   * @returns {boolean} True if form passes validation
   */
  const validateForm = (): boolean => {
    if (!stripe) {
      return false;
    }

    if (!acceptedTerms) {
      return false;
    }

    if (cardError) {
      return false;
    }

    // Either express checkout is ready, or manual form is complete
    if (expressCheckoutReady) {
      return true;
    }

    if (!cardComplete || !addressComplete) {
      return false;
    }

    return true;
  };

  return {
    cardComplete,
    addressComplete,
    acceptedTerms,
    expressCheckoutReady,
    isFormValid,
    setCardComplete,
    setAddressComplete,
    setAcceptedTerms,
    setExpressCheckoutReady,
    setCardError,
    validateForm,
  };
};