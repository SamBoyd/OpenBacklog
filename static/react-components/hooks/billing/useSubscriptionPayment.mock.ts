import { fn } from '@storybook/test';
import type { UseSubscriptionPaymentReturn } from './useSubscriptionPayment';

/**
 * Mock implementation of useSubscriptionPayment for Storybook
 * Provides different scenarios for testing UI states
 */
export const useSubscriptionPayment = fn((): UseSubscriptionPaymentReturn => ({
  isProcessing: false,
  errorMessage: null,
  handleSubmit: fn(async () => {
    // Mock successful payment processing
    console.log('Mock payment processing');
  }),
  handleExpressCheckout: fn(async (event: any) => {
    // Mock successful express checkout processing
    console.log('Mock express checkout processing', event);
  }),
  clearError: fn(() => {
    console.log('Mock clearing error');
  }),
})).mockName('useSubscriptionPayment');

/**
 * Mock for processing state
 */
export const useSubscriptionPaymentProcessing = fn((): UseSubscriptionPaymentReturn => ({
  isProcessing: true,
  errorMessage: null,
  handleSubmit: fn(async () => {
    // Mock processing state
  }),
  handleExpressCheckout: fn(async () => {
    // Mock express processing state
  }),
  clearError: fn(),
})).mockName('useSubscriptionPaymentProcessing');

/**
 * Mock for error state
 */
export const useSubscriptionPaymentError = fn((): UseSubscriptionPaymentReturn => ({
  isProcessing: false,
  errorMessage: 'Your card was declined. Please try a different payment method.',
  handleSubmit: fn(async () => {
    // Mock error handling
  }),
  handleExpressCheckout: fn(async () => {
    // Mock express error handling
  }),
  clearError: fn(() => {
    console.log('Mock clearing error');
  }),
})).mockName('useSubscriptionPaymentError');

/**
 * Mock for network error state
 */
export const useSubscriptionPaymentNetworkError = fn((): UseSubscriptionPaymentReturn => ({
  isProcessing: false,
  errorMessage: 'Network error. Please check your connection and try again.',
  handleSubmit: fn(async () => {
    // Mock network error
  }),
  handleExpressCheckout: fn(async () => {
    // Mock express network error
  }),
  clearError: fn(),
})).mockName('useSubscriptionPaymentNetworkError');