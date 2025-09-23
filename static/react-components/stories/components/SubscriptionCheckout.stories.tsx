import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';

import SubscriptionCheckout from '#components/billing/SubscriptionCheckout';
import {
  useSubscriptionPayment,
  useSubscriptionPaymentProcessing,
  useSubscriptionPaymentError,
  useSubscriptionPaymentNetworkError,
} from '#hooks/billing/useSubscriptionPayment.mock';
import {
  usePaymentForm,
  usePaymentFormIncompleteCard,
  usePaymentFormIncompleteAddress,
  usePaymentFormTermsNotAccepted,
  usePaymentFormInvalid,
  usePaymentFormExpressCheckoutReady,
} from '#hooks/billing/usePaymentForm.mock';

// Create a fake Stripe instance for Storybook
const stripePromise = loadStripe('pk_test_fake_key_for_storybook');

/**
 * Wrapper component to provide Stripe context
 */
const StripeWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Elements stripe={stripePromise}>
    <div className="max-w-2xl mx-auto p-6 bg-background">
      {children}
    </div>
  </Elements>
);

const meta: Meta<typeof SubscriptionCheckout> = {
  title: 'Components/Billing/SubscriptionCheckout',
  component: SubscriptionCheckout,
  decorators: [(Story) => <StripeWrapper><Story /></StripeWrapper>],
  parameters: {
    layout: 'fullscreen',
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#f8fafc' },
        { name: 'dark', value: '#0f172a' },
      ],
    },
  },
  tags: ['autodocs'],
  argTypes: {
    onCancel: { action: 'cancelled' },
    onSuccess: { action: 'success' },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

const defaultArgs = {
  onCancel: () => console.log('Payment cancelled'),
  onSuccess: () => console.log('Payment successful'),
};

/**
 * Default checkout form - ready to submit
 */
export const Default: Story = {
  args: defaultArgs,
  parameters: {
    msw: {
      handlers: [],
    },
    docs: {
      description: {
        story: 'Default state showing a complete checkout form ready for submission with valid card and accepted terms.',
      },
    },
  },
  beforeEach: () => {
    // Use default mocks
    useSubscriptionPayment.mockImplementation(() => ({
      isProcessing: false,
      errorMessage: null,
      handleSubmit: async () => {
        console.log('Mock payment processing');
      },
      handleExpressCheckout: async () => {
        console.log('Mock express checkout processing');
      },
      clearError: () => console.log('Mock clearing error'),
    }));

    usePaymentForm.mockImplementation(() => ({
      cardComplete: true,
      addressComplete: true,
      acceptedTerms: true,
      expressCheckoutReady: false,
      isFormValid: true,
      setCardComplete: () => {},
      setAddressComplete: () => {},
      setAcceptedTerms: () => {},
      setExpressCheckoutReady: () => {},
      setCardError: () => {},
      validateForm: () => true,
    }));
  },
};

/**
 * Processing state - payment in progress
 */
export const Processing: Story = {
  args: defaultArgs,
  parameters: {
    docs: {
      description: {
        story: 'Shows the checkout form during payment processing with disabled submit button and loading state.',
      },
    },
  },
  beforeEach: () => {
    useSubscriptionPaymentProcessing.mockImplementation(() => ({
      isProcessing: true,
      errorMessage: null,
      handleExpressCheckout: async () => {},
      handleSubmit: async () => {},
      clearError: () => {},
    }));

    usePaymentForm.mockImplementation(() => ({
      cardComplete: true,
      addressComplete: true,
      acceptedTerms: true,
      expressCheckoutReady: false,
      isFormValid: true,
      setCardComplete: () => {},
      setAddressComplete: () => {},
      setAcceptedTerms: () => {},
      setExpressCheckoutReady: () => {},
      setCardError: () => {},
      validateForm: () => true,
    }));
  },
};

/**
 * Payment error state - card declined
 */
export const PaymentError: Story = {
  args: defaultArgs,
  parameters: {
    docs: {
      description: {
        story: 'Shows the checkout form with a payment error message, such as card declined.',
      },
    },
  },
  beforeEach: () => {
    useSubscriptionPaymentError.mockImplementation(() => ({
      isProcessing: false,
      errorMessage: 'Your card was declined. Please try a different payment method.',
      handleSubmit: async () => {},
      handleExpressCheckout: async () => {},
      clearError: () => console.log('Mock clearing error'),
    }));

    usePaymentForm.mockImplementation(() => ({
      cardComplete: true,
      addressComplete: true,
      acceptedTerms: true,
      expressCheckoutReady: false,
      isFormValid: true,
      setCardComplete: () => {},
      setAddressComplete: () => {},
      setAcceptedTerms: () => {},
      setExpressCheckoutReady: () => {},
      setCardError: () => {},
      validateForm: () => true,
    }));
  },
};

/**
 * Network error state
 */
export const NetworkError: Story = {
  args: defaultArgs,
  parameters: {
    docs: {
      description: {
        story: 'Shows the checkout form with a network error message.',
      },
    },
  },
  beforeEach: () => {
    useSubscriptionPaymentNetworkError.mockImplementation(() => ({
      isProcessing: false,
      errorMessage: 'Network error. Please check your connection and try again.',
      handleSubmit: async () => {},
      handleExpressCheckout: async () => {},
      clearError: () => {},
    }));

    usePaymentForm.mockImplementation(() => ({
      cardComplete: true,
      addressComplete: true,
      acceptedTerms: true,
      expressCheckoutReady: false,
      isFormValid: true,
      setCardComplete: () => {},
      setAddressComplete: () => {},
      setAcceptedTerms: () => {},
      setExpressCheckoutReady: () => {},
      setCardError: () => {},
      validateForm: () => true,
    }));
  },
};

/**
 * Incomplete card state - form validation
 */
export const IncompleteCard: Story = {
  args: defaultArgs,
  parameters: {
    docs: {
      description: {
        story: 'Shows the checkout form with an incomplete card, submit button disabled due to validation.',
      },
    },
  },
  beforeEach: () => {
    useSubscriptionPayment.mockImplementation(() => ({
      isProcessing: false,
      errorMessage: null,
      handleSubmit: async () => {},
      handleExpressCheckout: async () => {},
      clearError: () => {},
    }));

    usePaymentFormIncompleteCard.mockImplementation(() => ({
      cardComplete: false,
      addressComplete: true,
      acceptedTerms: true,
      expressCheckoutReady: false,
      isFormValid: false,
      setCardComplete: () => {},
      setAddressComplete: () => {},
      setAcceptedTerms: () => {},
      setExpressCheckoutReady: () => {},
      setCardError: () => {},
      validateForm: () => false,
    }));
  },
};

/**
 * Incomplete address state
 */
export const IncompleteAddress: Story = {
  args: defaultArgs,
  parameters: {
    docs: {
      description: {
        story: 'Shows the checkout form with an incomplete address, submit button disabled due to validation.',
      },
    },
  },
  beforeEach: () => {
    useSubscriptionPayment.mockImplementation(() => ({
      isProcessing: false,
      errorMessage: null,
      handleSubmit: async () => {},
      handleExpressCheckout: async () => {},
      clearError: () => {},
    }));

    usePaymentFormIncompleteAddress.mockImplementation(() => ({
      cardComplete: true,
      addressComplete: false,
      acceptedTerms: true,
      expressCheckoutReady: false,
      isFormValid: false,
      setCardComplete: () => {},
      setAddressComplete: () => {},
      setAcceptedTerms: () => {},
      setExpressCheckoutReady: () => {},
      setCardError: () => {},
      validateForm: () => false,
    }));
  },
};

/**
 * Terms not accepted state
 */
export const TermsNotAccepted: Story = {
  args: defaultArgs,
  parameters: {
    docs: {
      description: {
        story: 'Shows the checkout form with terms not accepted, submit button disabled.',
      },
    },
  },
  beforeEach: () => {
    useSubscriptionPayment.mockImplementation(() => ({
      isProcessing: false,
      errorMessage: null,
      handleSubmit: async () => {},
      handleExpressCheckout: async () => {},
      clearError: () => {},
    }));

    usePaymentFormTermsNotAccepted.mockImplementation(() => ({
      cardComplete: true,
      addressComplete: true,
      acceptedTerms: false,
      expressCheckoutReady: false,
      isFormValid: false,
      setCardComplete: () => {},
      setAddressComplete: () => {},
      setAcceptedTerms: () => {},
      setExpressCheckoutReady: () => {},
      setCardError: () => {},
      validateForm: () => false,
    }));
  },
};

/**
 * Completely invalid form state
 */
export const InvalidForm: Story = {
  args: defaultArgs,
  parameters: {
    docs: {
      description: {
        story: 'Shows the checkout form in a completely invalid state - no card details and terms not accepted.',
      },
    },
  },
  beforeEach: () => {
    useSubscriptionPayment.mockImplementation(() => ({
      isProcessing: false,
      errorMessage: null,
      handleSubmit: async () => {},
      handleExpressCheckout: async () => {},
      clearError: () => {},
    }));

    usePaymentFormInvalid.mockImplementation(() => ({
      cardComplete: false,
      addressComplete: false,
      acceptedTerms: false,
      expressCheckoutReady: false,
      isFormValid: false,
      setCardComplete: () => {},
      setAddressComplete: () => {},
      setAcceptedTerms: () => {},
      setExpressCheckoutReady: () => {},
      setCardError: () => {},
      validateForm: () => false,
    }));
  },
};

/**
 * Express Checkout Ready - Shows express payment options
 */
export const ExpressCheckoutReady: Story = {
  args: defaultArgs,
  parameters: {
    docs: {
      description: {
        story: 'Shows the checkout form with express checkout options available (Apple Pay, Google Pay, etc.). Manual form is hidden by default.',
      },
    },
  },
  beforeEach: () => {
    useSubscriptionPayment.mockImplementation(() => ({
      isProcessing: false,
      errorMessage: null,
      handleSubmit: async () => {
        console.log('Mock payment processing');
      },
      handleExpressCheckout: async () => {
        console.log('Mock express checkout processing');
      },
      clearError: () => console.log('Mock clearing error'),
    }));

    usePaymentFormExpressCheckoutReady.mockImplementation(() => ({
      cardComplete: false,
      addressComplete: false,
      acceptedTerms: true,
      expressCheckoutReady: true,
      isFormValid: true,
      setCardComplete: () => {},
      setAddressComplete: () => {},
      setAcceptedTerms: () => {},
      setExpressCheckoutReady: () => {},
      setCardError: () => {},
      validateForm: () => true,
    }));
  },
};

